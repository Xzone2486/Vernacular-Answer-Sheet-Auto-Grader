"""
API routes for reference answers, scoring, and score retrieval.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.domain import Question, ReferenceAnswer, Score, StudentAnswer
from app.scoring.engine import get_scoring_engine
from app.schemas.domain import (
    ReferenceAnswerCreate,
    ReferenceAnswerResponse,
    ScoreResponse,
    ScoringResultResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /reference-answers — create or update a reference answer
# ---------------------------------------------------------------------------

@router.post("/reference-answers", response_model=ReferenceAnswerResponse)
async def create_or_update_reference_answer(
    body: ReferenceAnswerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update a ReferenceAnswer for a given question_id.

    If a ReferenceAnswer already exists for the question, it is updated.
    """
    # Validate that the question exists
    q_result = await db.execute(select(Question).where(Question.id == body.question_id))
    question = q_result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question {body.question_id} not found.")

    # Check for existing reference answer
    ra_result = await db.execute(
        select(ReferenceAnswer).where(ReferenceAnswer.question_id == body.question_id)
    )
    existing = ra_result.scalars().first()

    if existing:
        existing.text = body.text
        existing.rubric_keywords = body.rubric_keywords
        await db.commit()
        await db.refresh(existing)
        logger.info("Updated reference answer for question_id=%d", body.question_id)
        return existing
    else:
        ref_answer = ReferenceAnswer(
            question_id=body.question_id,
            text=body.text,
            rubric_keywords=body.rubric_keywords,
        )
        db.add(ref_answer)
        await db.commit()
        await db.refresh(ref_answer)
        logger.info("Created reference answer id=%d for question_id=%d", ref_answer.id, body.question_id)
        return ref_answer


# ---------------------------------------------------------------------------
# POST /student-answers/{id}/score — run scoring
# ---------------------------------------------------------------------------

@router.post("/student-answers/{student_answer_id}/score", response_model=ScoringResultResponse)
async def score_student_answer(
    student_answer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Run the scoring engine on a StudentAnswer.

    Looks up the StudentAnswer's question → ReferenceAnswer, runs
    ``score_answer``, and creates/updates the Score row.
    """
    # Fetch student answer with its question
    sa_result = await db.execute(
        select(StudentAnswer)
        .options(
            selectinload(StudentAnswer.question).selectinload(Question.reference_answer),
            selectinload(StudentAnswer.score),
        )
        .where(StudentAnswer.id == student_answer_id)
    )
    student_answer = sa_result.scalars().first()
    if not student_answer:
        raise HTTPException(status_code=404, detail="Student answer not found.")

    if not student_answer.ocr_text:
        raise HTTPException(
            status_code=422,
            detail="Student answer has no OCR text. Run OCR first.",
        )

    # Get reference answer
    question = student_answer.question
    if not question:
        raise HTTPException(status_code=404, detail="Question not found for this student answer.")

    ref_answer = question.reference_answer
    if not ref_answer:
        raise HTTPException(
            status_code=404,
            detail=f"No reference answer found for question_id={question.id}. Create one first.",
        )

    # Run scoring engine
    engine = get_scoring_engine()
    result = engine.score_answer(
        student_text=student_answer.ocr_text,
        reference_text=ref_answer.text,
        max_marks=question.max_marks,
        rubric_keywords=ref_answer.rubric_keywords,
    )

    # Create or update Score row
    if student_answer.score:
        score_row = student_answer.score
        score_row.auto_score = result.awarded_marks
        score_row.similarity_score = result.similarity_score
        score_row.explanation = result.explanation
    else:
        score_row = Score(
            student_answer_id=student_answer_id,
            auto_score=result.awarded_marks,
            similarity_score=result.similarity_score,
            explanation=result.explanation,
        )
        db.add(score_row)

    await db.commit()
    await db.refresh(score_row)

    logger.info(
        "Scored student_answer_id=%d: %.2f/%.1f (similarity=%.4f)",
        student_answer_id, result.awarded_marks, result.max_marks, result.similarity_score,
    )

    return result


# ---------------------------------------------------------------------------
# GET /student-answers/{id}/score — retrieve stored score
# ---------------------------------------------------------------------------

@router.get("/student-answers/{student_answer_id}/score", response_model=ScoreResponse)
async def get_score(
    student_answer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return the stored Score for a given student answer."""
    result = await db.execute(
        select(Score).where(Score.student_answer_id == student_answer_id)
    )
    score = result.scalars().first()
    if not score:
        raise HTTPException(
            status_code=404,
            detail="No score found. Run scoring first.",
        )
    return score

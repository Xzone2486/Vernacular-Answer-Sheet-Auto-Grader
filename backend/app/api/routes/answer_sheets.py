"""
API routes for answer sheet upload, OCR processing, and retrieval.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.domain import AnswerSheet, StudentAnswer
from app.ocr.engine import get_ocr_engine
from app.ocr.exceptions import OCRError
from app.schemas.domain import (
    AnswerSheetResponse,
    BBoxRegion,
    OCRRequest,
    OCRRegionResultSchema,
    OCRResponse,
    StudentAnswerResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed upload MIME types
ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}


# ---------------------------------------------------------------------------
# POST /answer-sheets — upload an answer sheet image
# ---------------------------------------------------------------------------

@router.post("/", response_model=AnswerSheetResponse)
async def upload_answer_sheet(
    student_id: int = Form(...),
    exam_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Accept a multipart file upload, validate it, store the file, and
    create an ``AnswerSheet`` database row."""

    # --- Validate MIME type ---
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    # --- Read file and validate size ---
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents)} bytes). Max: {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # --- Build storage path: uploads/{exam_id}/{student_id}/{unique_filename} ---
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    relative_dir = Path(str(exam_id)) / str(student_id)
    full_dir = Path(settings.UPLOAD_DIR) / relative_dir
    full_dir.mkdir(parents=True, exist_ok=True)

    file_path = full_dir / unique_name
    file_path.write_bytes(contents)

    # Store the path relative to UPLOAD_DIR for portability
    stored_path = str(relative_dir / unique_name)

    # --- Create DB record ---
    answer_sheet = AnswerSheet(
        student_id=student_id,
        exam_id=exam_id,
        image_path=stored_path,
    )
    db.add(answer_sheet)
    await db.commit()
    await db.refresh(answer_sheet)

    logger.info(
        "Uploaded answer sheet id=%d for student=%d exam=%d → %s",
        answer_sheet.id, student_id, exam_id, stored_path,
    )
    return answer_sheet


# ---------------------------------------------------------------------------
# POST /answer-sheets/{id}/ocr — run OCR on a stored answer sheet
# ---------------------------------------------------------------------------

@router.post("/{answer_sheet_id}/ocr", response_model=OCRResponse)
async def run_ocr(
    answer_sheet_id: int,
    body: Optional[OCRRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger OCR on the stored image for a given AnswerSheet.

    Optionally accepts a list of ``{question_id, bbox}`` regions in the
    request body.  Creates / updates ``StudentAnswer`` rows with the
    extracted text and confidence.
    """

    # Fetch the answer sheet
    result = await db.execute(
        select(AnswerSheet)
        .options(selectinload(AnswerSheet.student_answers))
        .where(AnswerSheet.id == answer_sheet_id)
    )
    sheet = result.scalars().first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Answer sheet not found.")

    # Resolve the full image path
    image_full_path = str(Path(settings.UPLOAD_DIR) / sheet.image_path)

    # Build regions list for the engine
    regions = None
    if body and body.regions:
        regions = [
            {"question_id": r.question_id, "bbox": r.bbox}
            for r in body.regions
        ]

    # Run OCR
    try:
        engine = get_ocr_engine()
        ocr_result = engine.extract_text(image_full_path, regions=regions)
    except OCRError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # Persist results as StudentAnswer rows
    saved_answers = []
    for region in ocr_result.regions:
        student_answer = StudentAnswer(
            answer_sheet_id=answer_sheet_id,
            question_id=region.question_id,
            ocr_text=region.text,
            ocr_confidence=region.confidence,
        )
        db.add(student_answer)
        saved_answers.append(student_answer)

    await db.commit()

    # Refresh to get IDs
    for sa in saved_answers:
        await db.refresh(sa)

    return OCRResponse(
        answer_sheet_id=answer_sheet_id,
        regions=[
            OCRRegionResultSchema(
                question_id=r.question_id,
                text=r.text,
                confidence=r.confidence,
                processing_time_ms=r.processing_time_ms,
            )
            for r in ocr_result.regions
        ],
        total_processing_time_ms=ocr_result.total_processing_time_ms,
        student_answers=[
            StudentAnswerResponse.model_validate(sa) for sa in saved_answers
        ],
    )


# ---------------------------------------------------------------------------
# GET /answer-sheets/{id} — retrieve an answer sheet with OCR results
# ---------------------------------------------------------------------------

@router.get("/{answer_sheet_id}", response_model=AnswerSheetResponse)
async def get_answer_sheet(
    answer_sheet_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return an answer sheet with its associated StudentAnswer OCR results."""
    result = await db.execute(
        select(AnswerSheet)
        .options(selectinload(AnswerSheet.student_answers))
        .where(AnswerSheet.id == answer_sheet_id)
    )
    sheet = result.scalars().first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Answer sheet not found.")
    return sheet

from typing import Optional
from app.schemas.domain import PaginatedResponse

@router.get("/", response_model=PaginatedResponse[AnswerSheetResponse])
async def list_answer_sheets(
    exam_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List answer sheets, optionally filtered by exam_id."""
    from sqlalchemy import func
    query = select(AnswerSheet).options(selectinload(AnswerSheet.student_answers))
    total_query = select(func.count(AnswerSheet.id))
    
    if exam_id:
        query = query.where(AnswerSheet.exam_id == exam_id)
        total_query = total_query.where(AnswerSheet.exam_id == exam_id)
        
    total = (await db.execute(total_query)).scalar() or 0
    query = query.order_by(AnswerSheet.id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return PaginatedResponse(items=result.scalars().all(), total=total, limit=limit, offset=offset)

from pydantic import BaseModel
from app.schemas.domain import BatchJobResponse
from app.core.jobs import JobTracker
from fastapi import BackgroundTasks
import asyncio

class BatchJobRequest(BaseModel):
    exam_id: int

async def process_batch_ocr(job_id: str, exam_id: int):
    tracker = JobTracker()
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.domain import AnswerSheet, StudentAnswer
        from sqlalchemy.orm import selectinload
        from app.ocr.engine import get_ocr_engine
        from pathlib import Path
        from app.core.config import settings
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AnswerSheet).options(selectinload(AnswerSheet.student_answers)).where(AnswerSheet.exam_id == exam_id)
            )
            sheets = result.scalars().all()
            sheets_to_process = [s for s in sheets if not s.student_answers]
            
            tracker._jobs[job_id].total = len(sheets_to_process)
            if not sheets_to_process:
                tracker.complete_job(job_id, result="No sheets pending OCR")
                return
            
            engine = get_ocr_engine()
            for i, sheet in enumerate(sheets_to_process):
                image_full_path = str(Path(settings.UPLOAD_DIR) / sheet.image_path)
                try:
                    ocr_result = engine.extract_text(image_full_path)
                    for region in ocr_result.regions:
                        qid = region.question_id if region.question_id else 1
                        sa = StudentAnswer(answer_sheet_id=sheet.id, question_id=qid, ocr_text=region.text, ocr_confidence=region.confidence)
                        session.add(sa)
                except Exception as e:
                    logger.error(f"OCR failed for sheet {sheet.id}: {e}")
                
                await session.commit()
                tracker.update_progress(job_id, i + 1)
            tracker.complete_job(job_id)
    except Exception as e:
        tracker.fail_job(job_id, str(e))

async def process_batch_score(job_id: str, exam_id: int):
    tracker = JobTracker()
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.domain import StudentAnswer, Question, Score
        from sqlalchemy.orm import selectinload
        from app.scoring.engine import get_scoring_engine
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(StudentAnswer)
                .join(StudentAnswer.answer_sheet)
                .where(StudentAnswer.answer_sheet.has(exam_id=exam_id))
                .options(selectinload(StudentAnswer.question).selectinload(Question.reference_answer), selectinload(StudentAnswer.score))
            )
            answers = result.scalars().all()
            answers_to_process = [a for a in answers if not a.score and a.ocr_text]
            
            tracker._jobs[job_id].total = len(answers_to_process)
            if not answers_to_process:
                tracker.complete_job(job_id, result="No answers pending score")
                return
                
            engine = get_scoring_engine()
            for i, sa in enumerate(answers_to_process):
                q = sa.question
                ref = q.reference_answer if q else None
                if ref and sa.ocr_text:
                    try:
                        res = engine.score_answer(student_text=sa.ocr_text, reference_text=ref.text, max_marks=q.max_marks, rubric_keywords=ref.rubric_keywords)
                        score_row = Score(student_answer_id=sa.id, auto_score=res.awarded_marks, similarity_score=res.similarity_score, explanation=res.explanation)
                        session.add(score_row)
                        await session.commit()
                    except Exception as e:
                        logger.error(f"Scoring failed for student answer {sa.id}: {e}")
                
                tracker.update_progress(job_id, i + 1)
            tracker.complete_job(job_id)
    except Exception as e:
        tracker.fail_job(job_id, str(e))

@router.post("/batch/ocr", response_model=BatchJobResponse)
async def batch_ocr(request: BatchJobRequest, bg_tasks: BackgroundTasks):
    tracker = JobTracker()
    job_id = tracker.create_job(description=f"Batch OCR for Exam {request.exam_id}")
    bg_tasks.add_task(process_batch_ocr, job_id, request.exam_id)
    return BatchJobResponse(job_id=job_id)

@router.post("/batch/score", response_model=BatchJobResponse)
async def batch_score(request: BatchJobRequest, bg_tasks: BackgroundTasks):
    tracker = JobTracker()
    job_id = tracker.create_job(description=f"Batch Scoring for Exam {request.exam_id}")
    bg_tasks.add_task(process_batch_score, job_id, request.exam_id)
    return BatchJobResponse(job_id=job_id)

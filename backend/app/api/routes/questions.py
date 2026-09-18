from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.domain import Question
from app.schemas.domain import QuestionCreate, QuestionResponse

router = APIRouter()

@router.post("/", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db)):
    db_question = Question(exam_id=question.exam_id, text=question.text, max_marks=question.max_marks)
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question

@router.get("/", response_model=List[QuestionResponse])
async def list_questions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question))
    return result.scalars().all()

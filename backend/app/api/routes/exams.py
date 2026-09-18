from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.domain import Exam
from app.schemas.domain import ExamCreate, ExamResponse

router = APIRouter()

@router.post("/", response_model=ExamResponse)
async def create_exam(exam: ExamCreate, db: AsyncSession = Depends(get_db)):
    db_exam = Exam(name=exam.name)
    db.add(db_exam)
    await db.commit()
    await db.refresh(db_exam)
    return db_exam

@router.get("/", response_model=List[ExamResponse])
async def list_exams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exam))
    return result.scalars().all()

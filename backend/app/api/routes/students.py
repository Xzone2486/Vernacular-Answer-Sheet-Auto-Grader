"""
Full CRUD routes for Students — create, list (paginated), get, update, delete.
All endpoints require authentication.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_evaluator
from app.db.session import get_db
from app.models.domain import Student
from app.schemas.domain import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=StudentResponse, status_code=201)
async def create_student(
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
    _evaluator=Depends(get_current_evaluator),
):
    # Check for duplicate roll_no
    existing = await db.execute(select(Student).where(Student.roll_no == body.roll_no))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail=f"Roll number '{body.roll_no}' already exists.")

    student = Student(name=body.name, roll_no=body.roll_no)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("/", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _evaluator=Depends(get_current_evaluator),
):
    total_result = await db.execute(select(func.count(Student.id)))
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Student).order_by(Student.id).limit(limit).offset(offset)
    )
    items = result.scalars().all()
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _evaluator=Depends(get_current_evaluator),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    _evaluator=Depends(get_current_evaluator),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if body.name is not None:
        student.name = body.name
    if body.roll_no is not None:
        # Check for duplicate
        dup = await db.execute(
            select(Student).where(Student.roll_no == body.roll_no, Student.id != student_id)
        )
        if dup.scalars().first():
            raise HTTPException(status_code=409, detail=f"Roll number '{body.roll_no}' already exists.")
        student.roll_no = body.roll_no

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _evaluator=Depends(get_current_evaluator),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    await db.delete(student)
    await db.commit()

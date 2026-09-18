"""
Authentication routes — register and login.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.models.evaluator import Evaluator
from app.schemas.domain import EvaluatorRegister, EvaluatorLogin, TokenResponse, EvaluatorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=EvaluatorResponse, status_code=201)
async def register(body: EvaluatorRegister, db: AsyncSession = Depends(get_db)):
    """Register a new evaluator account."""
    # Check duplicate email
    existing = await db.execute(select(Evaluator).where(Evaluator.email == body.email))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    evaluator = Evaluator(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(evaluator)
    await db.commit()
    await db.refresh(evaluator)
    logger.info("Registered evaluator id=%d email=%s", evaluator.id, evaluator.email)
    return evaluator


@router.post("/login", response_model=TokenResponse)
async def login(body: EvaluatorLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    result = await db.execute(select(Evaluator).where(Evaluator.email == body.email))
    evaluator = result.scalars().first()

    if not evaluator or not verify_password(body.password, evaluator.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(data={"sub": str(evaluator.id), "email": evaluator.email})
    logger.info("Login successful for evaluator id=%d", evaluator.id)
    return TokenResponse(access_token=token)

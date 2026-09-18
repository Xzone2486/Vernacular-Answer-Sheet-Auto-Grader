"""
Authentication and authorization utilities.

Provides:
- Password hashing (bcrypt via passlib)
- JWT creation and validation (python-jose)
- ``get_current_evaluator`` FastAPI dependency for protecting routes
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

import bcrypt

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependency — get current authenticated evaluator
# ---------------------------------------------------------------------------

async def get_current_evaluator(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate the JWT, then load the Evaluator from the DB.

    Use as a dependency on any route that requires authentication::

        @router.post("/", ...)
        async def my_route(evaluator = Depends(get_current_evaluator)):
            ...
    """
    from app.models.evaluator import Evaluator  # avoid circular import

    payload = decode_access_token(token)
    evaluator_id: Optional[int] = payload.get("sub")
    if evaluator_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub' claim.",
        )

    result = await db.execute(select(Evaluator).where(Evaluator.id == int(evaluator_id)))
    evaluator = result.scalars().first()
    if not evaluator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Evaluator not found.",
        )
    return evaluator

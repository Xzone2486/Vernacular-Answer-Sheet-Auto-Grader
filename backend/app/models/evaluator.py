from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from app.models.base import Base
import enum


class EvaluatorRole(str, enum.Enum):
    ADMIN = "admin"
    EVALUATOR = "evaluator"


class Evaluator(Base):
    __tablename__ = "evaluators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(EvaluatorRole), default=EvaluatorRole.EVALUATOR, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

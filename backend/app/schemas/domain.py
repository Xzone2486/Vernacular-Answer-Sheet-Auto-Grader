"""Pydantic v2 request/response schemas for the API."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Generic, List, Optional, TypeVar
from datetime import datetime

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination envelope
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    """Consistent paginated list envelope used by all list endpoints."""
    items: List[T]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Auth / Evaluator schemas
# ---------------------------------------------------------------------------

class EvaluatorRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=128)

class EvaluatorLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EvaluatorResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Student schemas
# ---------------------------------------------------------------------------

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    roll_no: str = Field(..., min_length=1, max_length=50)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    roll_no: Optional[str] = Field(None, min_length=1, max_length=50)

class StudentResponse(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Exam schemas
# ---------------------------------------------------------------------------

class ExamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)

class ExamCreate(ExamBase):
    pass

class ExamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)

class ExamResponse(ExamBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QuestionBrief(BaseModel):
    id: int
    text: str
    max_marks: float
    model_config = ConfigDict(from_attributes=True)

class ExamDetailResponse(ExamResponse):
    """Exam with nested questions."""
    questions: List[QuestionBrief] = []


# ---------------------------------------------------------------------------
# Question schemas
# ---------------------------------------------------------------------------

class QuestionBase(BaseModel):
    text: str = Field(..., min_length=1)
    max_marks: float = Field(..., gt=0)

class QuestionCreate(QuestionBase):
    exam_id: int

class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1)
    max_marks: Optional[float] = Field(None, gt=0)

class QuestionResponse(QuestionBase):
    id: int
    exam_id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Student Answer schemas
# ---------------------------------------------------------------------------

class StudentAnswerResponse(BaseModel):
    id: int
    answer_sheet_id: int
    question_id: Optional[int] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Answer Sheet schemas
# ---------------------------------------------------------------------------

class AnswerSheetResponse(BaseModel):
    id: int
    student_id: int
    exam_id: int
    image_path: str
    upload_time: datetime
    student_answers: List[StudentAnswerResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# OCR request/response schemas
# ---------------------------------------------------------------------------

class BBoxRegion(BaseModel):
    """A bounding-box region for per-question OCR segmentation."""
    question_id: int
    bbox: List[float]  # [x, y, width, height]


class OCRRequest(BaseModel):
    """Optional request body for the OCR endpoint."""
    regions: Optional[List[BBoxRegion]] = None


class OCRRegionResultSchema(BaseModel):
    question_id: Optional[int] = None
    text: str
    confidence: float
    processing_time_ms: float


class OCRResponse(BaseModel):
    answer_sheet_id: int
    regions: List[OCRRegionResultSchema]
    total_processing_time_ms: float
    student_answers: List[StudentAnswerResponse] = []


# ---------------------------------------------------------------------------
# Reference Answer schemas
# ---------------------------------------------------------------------------

class ReferenceAnswerCreate(BaseModel):
    """Create or update a reference answer for a question."""
    question_id: int
    text: str = Field(..., min_length=1)
    rubric_keywords: Optional[List[str]] = None


class ReferenceAnswerResponse(BaseModel):
    id: int
    question_id: int
    text: str
    rubric_keywords: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Scoring schemas
# ---------------------------------------------------------------------------

class ScoringResultResponse(BaseModel):
    """Full scoring result returned by the scoring engine."""
    similarity_score: float
    awarded_marks: float
    max_marks: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    explanation: str
    needs_review: bool = False


class ScoreResponse(BaseModel):
    """Stored score for a student answer."""
    id: int
    student_answer_id: int
    auto_score: Optional[float] = None
    final_score: Optional[float] = None
    similarity_score: Optional[float] = None
    explanation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Batch operation schemas
# ---------------------------------------------------------------------------

class BatchUploadResult(BaseModel):
    """Result of a single file in a batch upload."""
    filename: str
    answer_sheet_id: Optional[int] = None
    error: Optional[str] = None

class BatchUploadResponse(BaseModel):
    """Response for batch upload endpoint."""
    uploaded: int
    failed: int
    results: List[BatchUploadResult]

class BatchJobResponse(BaseModel):
    """Response when a batch background job is started."""
    job_id: str
    description: str
    total: int
    status: str


# ---------------------------------------------------------------------------
# Job status schema
# ---------------------------------------------------------------------------

class JobStatusResponse(BaseModel):
    id: str
    status: str
    description: str
    created_at: datetime
    updated_at: datetime
    processed: int = 0
    total: int = 0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Error response schema (for OpenAPI docs)
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
    error_code: str

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import exams, questions, answer_sheets, scoring, auth, students

# Setup logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vernacular Answer-Sheet Auto-Grader API",
    description="API for auto-grading handwritten vernacular exam answers.",
    version="0.3.0",
)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Ensure upload directory exists and mount it for static file serving
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "environment": settings.ENV}

# Routers
app.include_router(exams.router, prefix="/api/v1/exams", tags=["exams"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])
app.include_router(answer_sheets.router, prefix="/api/v1/answer-sheets", tags=["answer-sheets"])
app.include_router(scoring.router, prefix="/api/v1", tags=["scoring"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(students.router, prefix="/api/v1/students", tags=["students"])
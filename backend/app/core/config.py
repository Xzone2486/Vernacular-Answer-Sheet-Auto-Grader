from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    LOG_LEVEL: str = "info"

    # Postgres
    DATABASE_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Scoring engine
    SCORING_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    SCORING_LOW_THRESHOLD: float = 0.3
    SCORING_HIGH_THRESHOLD: float = 0.8
    SCORING_KEYWORD_THRESHOLD: float = 0.5

    # JWT Authentication
    JWT_SECRET_KEY: str = "CHANGE-ME-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # Docs visibility (disable in production)
    DOCS_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

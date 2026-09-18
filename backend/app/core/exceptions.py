"""
Centralized application exceptions and FastAPI exception handlers.

All typed exceptions inherit from ``AppError`` and carry an HTTP status code
and a machine-readable error_code string.  The global exception handler
registered in ``main.py`` catches these and returns a consistent JSON
error envelope::

    {"detail": "...", "error_code": "NOT_FOUND"}
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class DuplicateError(AppError):
    def __init__(self, message: str = "Resource already exists."):
        super().__init__(message, status_code=409, error_code="DUPLICATE")


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed."):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied."):
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required."):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


# ---------------------------------------------------------------------------
# Global exception handler — register in main.py
# ---------------------------------------------------------------------------

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert any ``AppError`` into a consistent JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )

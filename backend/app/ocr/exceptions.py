"""
Typed exceptions for the OCR module.

These exceptions are designed to be caught by the API layer and translated
into clean HTTP error responses with appropriate status codes.
"""


class OCRError(Exception):
    """Base exception for all OCR-related errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ImageUnreadableError(OCRError):
    """Raised when the image file cannot be loaded or decoded.

    Typical causes: unsupported format, permissions issue, path doesn't exist.
    Maps to HTTP 400 (bad request — the client sent a bad file).
    """

    def __init__(self, message: str = "Image could not be read or decoded."):
        super().__init__(message, status_code=400)


class CorruptedFileError(OCRError):
    """Raised when the file exists but its contents are corrupted or truncated.

    Maps to HTTP 422 (unprocessable entity).
    """

    def __init__(self, message: str = "File appears to be corrupted or truncated."):
        super().__init__(message, status_code=422)


class NoTextDetectedError(OCRError):
    """Raised when OCR completes but extracts no meaningful text.

    This is not necessarily a system error — the image may genuinely be blank
    or contain only noise. Maps to HTTP 200 with an empty result in most flows,
    but can be raised as a 422 if the caller explicitly requires text.
    """

    def __init__(self, message: str = "No text could be detected in the image."):
        super().__init__(message, status_code=422)

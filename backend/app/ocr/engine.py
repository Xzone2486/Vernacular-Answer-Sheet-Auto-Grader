"""
OCR engine module — extracts Devanagari text from preprocessed answer sheet images.

Architecture
------------
This module defines an *abstract* ``OCREngine`` base class so that different
OCR backends can be swapped in without changing any calling code.  The current
production implementation is ``TesseractOCREngine`` which uses Google's
Tesseract with the Hindi (``hin``) trained data.

Extension Point — Adding a Transformer-Based Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add a new engine (e.g. a fine-tuned TrOCR or PaddleOCR model):

  1. Create a new class that inherits from ``OCREngine``.
  2. Implement ``extract_text(image_path, regions)``.
  3. Register it in your dependency injection or config layer so the API
     routes receive the new engine instance instead of ``TesseractOCREngine``.

No changes to the API routes, schemas, or frontend are required.

Hindi Tessdata Setup
~~~~~~~~~~~~~~~~~~~~
Tesseract needs the ``hin.traineddata`` file:
  - **Debian/Ubuntu**: ``apt-get install tesseract-ocr-hin``
  - **Manual**: Download from https://github.com/tesseract-ocr/tessdata_best
    and place in ``/usr/share/tesseract-ocr/5/tessdata/`` (or wherever
    ``TESSDATA_PREFIX`` points).
The project Dockerfile installs this automatically.
"""

import abc
import logging
import time
from typing import List, Optional

import numpy as np
import pytesseract
from pydantic import BaseModel

from .exceptions import ImageUnreadableError, NoTextDetectedError, CorruptedFileError
from .preprocess import preprocess_pipeline, segment_regions, load_image, to_grayscale

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

class OCRRegionResult(BaseModel):
    """OCR result for a single answer region."""
    question_id: Optional[int] = None
    text: str
    confidence: float
    processing_time_ms: float


class OCRResult(BaseModel):
    """Aggregate OCR result for an entire answer sheet."""
    regions: List[OCRRegionResult]
    total_processing_time_ms: float


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class OCREngine(abc.ABC):
    """Abstract interface for OCR engines.

    Any concrete engine must implement ``extract_text``.  This allows the
    system to transparently swap between Tesseract, PaddleOCR, TrOCR, or
    any future model without modifying the API layer.
    """

    @abc.abstractmethod
    def extract_text(
        self,
        image_path: str,
        regions: Optional[List[dict]] = None,
    ) -> OCRResult:
        """Extract text from an answer sheet image.

        Args:
            image_path: Filesystem path to the image.
            regions: Optional list of ``{"question_id": int, "bbox": [x,y,w,h]}``
                     dicts.  If not provided, the whole image is treated as one
                     region.

        Returns:
            An ``OCRResult`` containing per-region text, confidence, and timing.
        """
        ...


# ---------------------------------------------------------------------------
# Tesseract implementation
# ---------------------------------------------------------------------------

class TesseractOCREngine(OCREngine):
    """OCR engine backed by Tesseract with Hindi (Devanagari) support.

    Uses ``pytesseract`` to invoke Tesseract in ``--oem 1`` (LSTM) mode
    with ``--psm 6`` (assume a single uniform block of text) by default.
    Confidence is derived by averaging the word-level confidences that
    Tesseract reports.
    """

    def __init__(self, lang: str = "hin", psm: int = 6, oem: int = 1):
        self.lang = lang
        self.config = f"--oem {oem} --psm {psm}"

    # ---- public API -------------------------------------------------------

    def extract_text(
        self,
        image_path: str,
        regions: Optional[List[dict]] = None,
    ) -> OCRResult:
        total_start = time.perf_counter()

        # Preprocess the full image
        try:
            preprocessed = preprocess_pipeline(image_path)
        except (ImageUnreadableError, CorruptedFileError):
            raise  # let typed exceptions propagate
        except Exception as exc:
            raise ImageUnreadableError(f"Preprocessing failed: {exc}")

        # Segment into per-question regions (or whole-image)
        segmented = segment_regions(preprocessed, regions)

        region_results: List[OCRRegionResult] = []
        for question_id, region_img in segmented:
            region_start = time.perf_counter()
            text, confidence = self._ocr_region(region_img)
            elapsed_ms = (time.perf_counter() - region_start) * 1000

            region_results.append(
                OCRRegionResult(
                    question_id=question_id,
                    text=text,
                    confidence=round(confidence, 2),
                    processing_time_ms=round(elapsed_ms, 1),
                )
            )

        total_ms = (time.perf_counter() - total_start) * 1000

        result = OCRResult(
            regions=region_results,
            total_processing_time_ms=round(total_ms, 1),
        )

        # Warn if nothing was extracted at all
        if all(r.text.strip() == "" for r in result.regions):
            logger.warning("No text detected in any region for image: %s", image_path)

        return result

    # ---- internal helpers -------------------------------------------------

    def _ocr_region(self, img: np.ndarray) -> tuple[str, float]:
        """Run Tesseract on a single image region.

        Returns:
            Tuple of (extracted_text, average_confidence).
        """
        try:
            # Get detailed word-level data for confidence computation
            data = pytesseract.image_to_data(
                img, lang=self.lang, config=self.config, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractNotFoundError:
            raise ImageUnreadableError(
                "Tesseract is not installed or not on PATH. "
                "Install with: apt-get install tesseract-ocr tesseract-ocr-hin"
            )
        except Exception as exc:
            raise CorruptedFileError(f"Tesseract failed on region: {exc}")

        # Extract words and their confidences (Tesseract uses -1 for non-word entries)
        words: List[str] = []
        confidences: List[float] = []

        for i, conf in enumerate(data["conf"]):
            conf_val = float(conf)
            text_val = str(data["text"][i]).strip()
            if conf_val > 0 and text_val:
                words.append(text_val)
                confidences.append(conf_val)

        extracted_text = " ".join(words)
        avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0

        return extracted_text, avg_confidence


# ---------------------------------------------------------------------------
# Module-level convenience: default engine instance
# ---------------------------------------------------------------------------

def get_ocr_engine() -> OCREngine:
    """Factory function returning the default OCR engine.

    This is the single point you change when swapping engines globally.
    In a larger system this would read from config / DI container.
    """
    return TesseractOCREngine()

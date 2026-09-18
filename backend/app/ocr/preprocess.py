"""
Image preprocessing pipeline for handwritten Devanagari answer sheets.

This module provides a chain of image processing steps to clean and prepare
scanned/photographed answer sheet images before OCR:
  1. Load image (jpg, png, or first page of a PDF)
  2. Convert to grayscale
  3. Deskew (detect and correct rotation)
  4. Denoise
  5. Normalize contrast (CLAHE)
  6. Binarize (adaptive thresholding)

It also provides a region segmentation utility that crops per-question areas
from a full answer sheet image given bounding boxes.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from .exceptions import ImageUnreadableError, CorruptedFileError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias for a bounding-box region specification
# ---------------------------------------------------------------------------
RegionSpec = dict  # {"question_id": int, "bbox": [x, y, w, h]}


# ---------------------------------------------------------------------------
# 1. Image loading
# ---------------------------------------------------------------------------

def load_image(path: str) -> np.ndarray:
    """Load an image from disk. Supports jpg, png, and single-page PDF.

    For PDF files, the first page is converted to an image using pdf2image
    (requires poppler-utils installed on the system).

    Args:
        path: Filesystem path to the image or PDF.

    Returns:
        The loaded image as a BGR numpy array (OpenCV format).

    Raises:
        ImageUnreadableError: If the file cannot be loaded.
        CorruptedFileError: If the file exists but is empty or corrupt.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise ImageUnreadableError(f"File not found: {path}")

    if file_path.stat().st_size == 0:
        raise CorruptedFileError(f"File is empty: {path}")

    suffix = file_path.suffix.lower()

    # --- PDF handling ---
    if suffix == ".pdf":
        try:
            from pdf2image import convert_from_path

            pages = convert_from_path(str(file_path), first_page=1, last_page=1, dpi=300)
            if not pages:
                raise CorruptedFileError("PDF contains no pages.")
            # Convert PIL Image → OpenCV BGR
            pil_img = pages[0]
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img
        except ImportError:
            raise ImageUnreadableError(
                "pdf2image is required for PDF support. Install it and poppler-utils."
            )
        except Exception as exc:
            raise CorruptedFileError(f"Failed to read PDF: {exc}")

    # --- Raster image handling (jpg, png, etc.) ---
    img = cv2.imread(str(file_path))
    if img is None:
        raise ImageUnreadableError(f"OpenCV could not decode the file: {path}")

    return img


# ---------------------------------------------------------------------------
# 2. Grayscale conversion
# ---------------------------------------------------------------------------

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert a BGR image to single-channel grayscale.

    If the image is already single-channel, it is returned as-is.
    """
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# ---------------------------------------------------------------------------
# 3. Deskew
# ---------------------------------------------------------------------------

def deskew(img: np.ndarray) -> np.ndarray:
    """Detect and correct rotation in a grayscale image.

    Uses cv2.minAreaRect on non-zero pixels after thresholding to estimate
    the skew angle, then applies an affine rotation to straighten the image.
    Only corrects angles within ±15° to avoid over-rotating.

    Args:
        img: Single-channel grayscale image.

    Returns:
        Deskewed grayscale image.
    """
    # Threshold to find text pixels
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    coords = np.column_stack(np.where(binary > 0))
    if coords.shape[0] < 50:
        # Not enough content to estimate angle — return unchanged
        return img

    angle = cv2.minAreaRect(coords)[-1]

    # minAreaRect returns angles in [-90, 0); normalise to skew angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only correct small skews
    if abs(angle) > 15 or abs(angle) < 0.5:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    logger.debug("Deskewed image by %.2f°", angle)
    return rotated


# ---------------------------------------------------------------------------
# 4. Denoising
# ---------------------------------------------------------------------------

def denoise(img: np.ndarray) -> np.ndarray:
    """Remove noise from a grayscale image using non-local means denoising."""
    return cv2.fastNlMeansDenoising(img, h=10, templateWindowSize=7, searchWindowSize=21)


# ---------------------------------------------------------------------------
# 5. Contrast normalisation (CLAHE)
# ---------------------------------------------------------------------------

def normalize_contrast(img: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation).

    This improves local contrast, making faint handwriting more visible
    without blowing out darker regions.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(img)


# ---------------------------------------------------------------------------
# 6. Binarisation
# ---------------------------------------------------------------------------

def binarize(img: np.ndarray) -> np.ndarray:
    """Apply adaptive Gaussian thresholding to produce a clean binary image.

    Adaptive thresholding handles uneven lighting across the page better
    than a global threshold.
    """
    return cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=15, C=10
    )


# ---------------------------------------------------------------------------
# Full preprocessing pipeline
# ---------------------------------------------------------------------------

def preprocess_pipeline(image_path: str) -> np.ndarray:
    """Run the full preprocessing pipeline on an answer sheet image.

    Steps: load → grayscale → deskew → denoise → contrast → binarize.

    Args:
        image_path: Path to the raw image file.

    Returns:
        Preprocessed binary image ready for OCR.
    """
    img = load_image(image_path)
    gray = to_grayscale(img)
    deskewed = deskew(gray)
    denoised = denoise(deskewed)
    contrasted = normalize_contrast(denoised)
    binary = binarize(contrasted)
    return binary


# ---------------------------------------------------------------------------
# Region segmentation
# ---------------------------------------------------------------------------

def segment_regions(
    img: np.ndarray, regions: Optional[List[RegionSpec]] = None
) -> List[Tuple[Optional[int], np.ndarray]]:
    """Segment an image into per-question regions.

    Args:
        img: The preprocessed image (any number of channels).
        regions: Optional list of dicts with keys ``question_id`` (int) and
                 ``bbox`` ([x, y, width, height]).  If *None* or empty, the
                 entire image is returned as a single region with
                 ``question_id=None``.

    Returns:
        List of ``(question_id, cropped_image)`` tuples.
    """
    if not regions:
        return [(None, img)]

    result: List[Tuple[Optional[int], np.ndarray]] = []
    h, w = img.shape[:2]

    for region in regions:
        qid = region.get("question_id")
        x, y, rw, rh = region["bbox"]
        # Clamp to image boundaries
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(w, int(x + rw))
        y2 = min(h, int(y + rh))
        cropped = img[y1:y2, x1:x2]
        if cropped.size == 0:
            logger.warning("Empty crop for question_id=%s bbox=%s", qid, region["bbox"])
            continue
        result.append((qid, cropped))

    return result

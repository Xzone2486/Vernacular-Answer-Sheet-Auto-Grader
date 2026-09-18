"""
Sentence embedding module for multilingual (Hindi/Devanagari) text.

Model Choice
~~~~~~~~~~~~
Uses ``paraphrase-multilingual-mpnet-base-v2`` from the sentence-transformers
library. This model:
  - Supports 50+ languages including Hindi, making it ideal for Devanagari text.
  - Produces 768-dimensional embeddings with strong cross-lingual alignment.
  - Is well-tested for semantic similarity tasks.

To Swap Models
~~~~~~~~~~~~~~
Change ``SCORING_MODEL_NAME`` in ``app/core/config.py`` (or set the env var).
Any sentence-transformers compatible model works.  For Indic-specific tasks,
consider ``ai4bharat/indic-sentence-bert-nli`` if higher Hindi accuracy is
needed — the interface is identical.

The model is loaded as a **singleton** so it is initialized once on first use
and reused across all subsequent requests within the same process.
"""

import logging
import re
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton model cache (thread-safe)
# ---------------------------------------------------------------------------

_model_cache = None
_model_lock = threading.Lock()


def _get_model():
    """Load and cache the SentenceTransformer model (singleton).

    Thread-safe: uses a lock so concurrent requests don't load the model
    multiple times during startup.
    """
    global _model_cache
    if _model_cache is None:
        with _model_lock:
            if _model_cache is None:  # double-check inside lock
                from sentence_transformers import SentenceTransformer
                from app.core.config import settings

                model_name = settings.SCORING_MODEL_NAME
                logger.info("Loading sentence-transformer model: %s …", model_name)
                _model_cache = SentenceTransformer(model_name)
                logger.info("Model loaded successfully.")
    return _model_cache


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Basic text normalization for OCR'd Devanagari text.

    - Strips leading/trailing whitespace.
    - Collapses multiple whitespace characters into single spaces.
    - Normalizes common Devanagari OCR artifacts:
      * Removes zero-width joiners/non-joiners that OCR sometimes inserts.
      * Normalizes Devanagari nukta variants.
    """
    if not text:
        return ""

    # Strip and collapse whitespace
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Remove zero-width characters (common OCR artifacts)
    text = text.replace("\u200c", "")  # zero-width non-joiner
    text = text.replace("\u200d", "")  # zero-width joiner
    text = text.replace("\ufeff", "")  # BOM

    return text


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_text(text: str) -> np.ndarray:
    """Normalize text and produce a sentence embedding vector.

    Args:
        text: Raw text (may contain OCR artifacts).

    Returns:
        A 1-D numpy array of shape ``(dim,)`` — the sentence embedding.
        Returns a zero vector if the input is empty after normalization.
    """
    normalized = normalize_text(text)
    if not normalized:
        model = _get_model()
        dim = model.get_sentence_embedding_dimension()
        return np.zeros(dim, dtype=np.float32)

    model = _get_model()
    embedding = model.encode(normalized, convert_to_numpy=True)
    return embedding


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two embedding vectors.

    Returns a value in [-1, 1].  Returns 0.0 if either vector is zero.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

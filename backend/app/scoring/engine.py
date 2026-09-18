"""
Semantic scoring engine — compares student answers against reference answers.

Architecture
------------
Defines an abstract ``ScoringEngine`` base class so alternative scoring
strategies (e.g. LLM-based grading, keyword-only grading) can be added later
without touching calling code.

The production implementation is ``EmbeddingScoringEngine`` which:
  1. Embeds student and reference text using a multilingual sentence-transformer.
  2. Computes cosine similarity as the base similarity score.
  3. Maps similarity to marks via a configurable threshold curve.
  4. Optionally checks rubric keyword presence (semantic, not substring).
  5. Generates a human-readable explanation.

Extension Point — Adding Alternative Scoring Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add a new engine (e.g. an LLM-based grader):
  1. Create a class inheriting from ``ScoringEngine``.
  2. Implement ``score_answer()``.
  3. Swap ``get_scoring_engine()`` to return the new class.
No API, schema, or frontend changes required.
"""

import abc
import logging
from typing import List, Optional

from pydantic import BaseModel

from .embed import embed_text, compute_cosine_similarity, normalize_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

class ScoringResult(BaseModel):
    """Full result of scoring a student answer against a reference."""

    similarity_score: float        # raw cosine similarity [-1, 1]
    awarded_marks: float           # marks out of max_marks
    max_marks: float               # the question's max marks
    matched_keywords: List[str]    # rubric keywords found in student text
    missing_keywords: List[str]    # rubric keywords NOT found
    explanation: str               # human-readable explanation
    needs_review: bool = False     # True if answer should be flagged for manual review


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class ScoringEngine(abc.ABC):
    """Abstract interface for scoring engines."""

    @abc.abstractmethod
    def score_answer(
        self,
        student_text: str,
        reference_text: str,
        max_marks: float,
        rubric_keywords: Optional[List[str]] = None,
    ) -> ScoringResult:
        """Score a student's answer against a reference answer.

        Args:
            student_text: The OCR-extracted student answer text.
            reference_text: The reference/model answer text.
            max_marks: Maximum marks for this question.
            rubric_keywords: Optional list of key concepts to check for.

        Returns:
            A ``ScoringResult`` with marks, similarity, keywords, and explanation.
        """
        ...


# ---------------------------------------------------------------------------
# Embedding-based implementation
# ---------------------------------------------------------------------------

class EmbeddingScoringEngine(ScoringEngine):
    """Scoring engine using multilingual sentence embeddings.

    Similarity-to-Marks Threshold Curve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The raw cosine similarity (typically 0.2–1.0 for related text) is mapped
    to marks using a piecewise-linear function:

      - Below ``low_threshold`` → 0 marks
      - Above ``high_threshold`` → full marks
      - Between → linear interpolation

    These thresholds are configurable via ``Settings`` (env vars or .env file).
    Tune them based on empirical correlation with human-assigned scores.

    Keyword Matching
    ~~~~~~~~~~~~~~~~
    If rubric keywords are provided, each keyword is embedded and compared
    against the student text embedding. Keywords with similarity above
    ``keyword_threshold`` are considered "matched". This is **semantic**
    matching — "प्रकाश संश्लेषण" will match "photosynthesis" because the
    multilingual model aligns cross-lingual semantics.
    """

    def __init__(
        self,
        low_threshold: float = 0.3,
        high_threshold: float = 0.8,
        keyword_threshold: float = 0.5,
    ):
        # --- Configurable thresholds ---
        # low_threshold:  cosine similarity below this → 0 marks
        # high_threshold: cosine similarity above this → full marks
        # keyword_threshold: per-keyword similarity above this → "matched"
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.keyword_threshold = keyword_threshold

    def score_answer(
        self,
        student_text: str,
        reference_text: str,
        max_marks: float,
        rubric_keywords: Optional[List[str]] = None,
    ) -> ScoringResult:

        # --- Edge case: empty / near-empty student text ---
        normalized_student = normalize_text(student_text)
        if not normalized_student or len(normalized_student) < 3:
            return ScoringResult(
                similarity_score=0.0,
                awarded_marks=0.0,
                max_marks=max_marks,
                matched_keywords=[],
                missing_keywords=rubric_keywords or [],
                explanation=(
                    "Student answer is empty or too short to evaluate. "
                    "Flagged for manual review."
                ),
                needs_review=True,
            )

        # --- Edge case: identical text → full marks ---
        normalized_ref = normalize_text(reference_text)
        if normalized_student == normalized_ref:
            return ScoringResult(
                similarity_score=1.0,
                awarded_marks=max_marks,
                max_marks=max_marks,
                matched_keywords=rubric_keywords or [],
                missing_keywords=[],
                explanation="Student answer is identical to the reference answer. Full marks awarded.",
                needs_review=False,
            )

        # --- Compute cosine similarity ---
        student_emb = embed_text(student_text)
        reference_emb = embed_text(reference_text)
        similarity = compute_cosine_similarity(student_emb, reference_emb)

        # --- Map similarity to marks (piecewise-linear) ---
        awarded_marks = self._similarity_to_marks(similarity, max_marks)

        # --- Keyword matching (semantic) ---
        matched_keywords: List[str] = []
        missing_keywords: List[str] = []

        if rubric_keywords:
            for keyword in rubric_keywords:
                kw_emb = embed_text(keyword)
                kw_sim = compute_cosine_similarity(student_emb, kw_emb)
                if kw_sim >= self.keyword_threshold:
                    matched_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

        # --- Generate explanation ---
        explanation = self._build_explanation(
            similarity, awarded_marks, max_marks, matched_keywords, missing_keywords
        )

        # Flag for review if score is very low but there was content
        needs_review = awarded_marks == 0.0 and len(normalized_student) > 10

        return ScoringResult(
            similarity_score=round(similarity, 4),
            awarded_marks=round(awarded_marks, 2),
            max_marks=max_marks,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            explanation=explanation,
            needs_review=needs_review,
        )

    def _similarity_to_marks(self, similarity: float, max_marks: float) -> float:
        """Map cosine similarity to marks using a piecewise-linear threshold curve.

        Below low_threshold → 0 marks.
        Above high_threshold → full marks.
        Between → linear interpolation.
        """
        if similarity <= self.low_threshold:
            return 0.0
        if similarity >= self.high_threshold:
            return max_marks

        # Linear interpolation between thresholds
        proportion = (similarity - self.low_threshold) / (self.high_threshold - self.low_threshold)
        return round(proportion * max_marks, 2)

    def _build_explanation(
        self,
        similarity: float,
        awarded_marks: float,
        max_marks: float,
        matched_keywords: List[str],
        missing_keywords: List[str],
    ) -> str:
        """Build a human-readable explanation of the scoring result."""
        parts: List[str] = []

        # Similarity description
        sim_pct = round(similarity * 100, 1)
        if similarity >= 0.8:
            parts.append(f"High semantic overlap with reference answer ({sim_pct}% similarity).")
        elif similarity >= 0.5:
            parts.append(f"Moderate semantic overlap with reference answer ({sim_pct}% similarity).")
        elif similarity >= 0.3:
            parts.append(f"Low semantic overlap with reference answer ({sim_pct}% similarity).")
        else:
            parts.append(f"Very low semantic overlap with reference answer ({sim_pct}% similarity).")

        # Marks
        parts.append(f"Awarded {awarded_marks}/{max_marks} marks.")

        # Keywords
        if matched_keywords:
            parts.append(f"Key concepts found: {', '.join(matched_keywords)}.")
        if missing_keywords:
            parts.append(f"Missing key concepts: {', '.join(missing_keywords)}.")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def get_scoring_engine() -> ScoringEngine:
    """Return the default scoring engine, configured from settings.

    This is the single point to change when swapping engines globally.
    """
    from app.core.config import settings

    return EmbeddingScoringEngine(
        low_threshold=settings.SCORING_LOW_THRESHOLD,
        high_threshold=settings.SCORING_HIGH_THRESHOLD,
        keyword_threshold=settings.SCORING_KEYWORD_THRESHOLD,
    )

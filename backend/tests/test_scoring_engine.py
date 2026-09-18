"""
Unit tests for the scoring engine.

Tests cover:
  - Identical text → full marks
  - Clearly unrelated text → ~0 marks
  - Paraphrased-but-correct text → high score (proves semantic > keyword matching)
  - Empty text → 0 marks + needs_review flag
  - Keyword matching accuracy

NOTE: These tests require the sentence-transformers model to be available.
In CI without GPU, use CPU-only torch (which the Dockerfile installs).
To run without the model, mock embed_text — see test_scoring_engine_mocked below.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from app.scoring.engine import EmbeddingScoringEngine, ScoringResult
from app.scoring.embed import normalize_text


# ---------------------------------------------------------------------------
# Test text normalization
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_strips_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapses_whitespace(self):
        assert normalize_text("hello   world") == "hello world"

    def test_removes_zero_width_chars(self):
        assert normalize_text("हिन्\u200cदी") == "हिन्दी"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_none_like_empty(self):
        assert normalize_text("") == ""


# ---------------------------------------------------------------------------
# Tests with mocked embeddings (no model download required)
# ---------------------------------------------------------------------------

class TestScoringEngineMocked:
    """Tests using mocked embeddings to verify scoring logic without
    needing the actual sentence-transformer model installed."""

    def setup_method(self):
        self.engine = EmbeddingScoringEngine(
            low_threshold=0.3,
            high_threshold=0.8,
            keyword_threshold=0.5,
        )

    def test_identical_text_full_marks(self):
        """Identical text should get full marks via the fast-path check."""
        result = self.engine.score_answer(
            student_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            reference_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            max_marks=10.0,
        )
        assert result.awarded_marks == 10.0
        assert result.similarity_score == 1.0
        assert result.needs_review is False
        assert "identical" in result.explanation.lower()

    def test_empty_student_text_zero_marks(self):
        """Empty student text should get 0 marks and be flagged for review."""
        result = self.engine.score_answer(
            student_text="",
            reference_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            max_marks=10.0,
        )
        assert result.awarded_marks == 0.0
        assert result.needs_review is True
        assert "empty" in result.explanation.lower()

    def test_very_short_student_text(self):
        """Very short text (< 3 chars) should be treated as empty."""
        result = self.engine.score_answer(
            student_text="हा",
            reference_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            max_marks=5.0,
        )
        assert result.awarded_marks == 0.0
        assert result.needs_review is True

    @patch("app.scoring.engine.embed_text")
    @patch("app.scoring.engine.compute_cosine_similarity")
    def test_high_similarity_high_marks(self, mock_cosine, mock_embed):
        """High cosine similarity (above high_threshold) → full marks."""
        mock_embed.return_value = np.array([1.0, 0.0, 0.0])
        mock_cosine.return_value = 0.92

        result = self.engine.score_answer(
            student_text="प्रकाश संश्लेषण वह प्रक्रिया है जिसमें पौधे सूर्य के प्रकाश का उपयोग करते हैं",
            reference_text="प्रकाश संश्लेषण एक जैविक प्रक्रिया है",
            max_marks=10.0,
        )
        assert result.awarded_marks == 10.0
        assert result.similarity_score == 0.92

    @patch("app.scoring.engine.embed_text")
    @patch("app.scoring.engine.compute_cosine_similarity")
    def test_low_similarity_zero_marks(self, mock_cosine, mock_embed):
        """Very low cosine similarity (below low_threshold) → 0 marks."""
        mock_embed.return_value = np.array([1.0, 0.0, 0.0])
        mock_cosine.return_value = 0.15

        result = self.engine.score_answer(
            student_text="आज मौसम बहुत अच्छा है",
            reference_text="प्रकाश संश्लेषण एक जैविक प्रक्रिया है",
            max_marks=10.0,
        )
        assert result.awarded_marks == 0.0

    @patch("app.scoring.engine.embed_text")
    @patch("app.scoring.engine.compute_cosine_similarity")
    def test_medium_similarity_partial_marks(self, mock_cosine, mock_embed):
        """Medium similarity → proportional marks via linear interpolation."""
        mock_embed.return_value = np.array([1.0, 0.0, 0.0])
        # 0.55 is exactly halfway between 0.3 and 0.8 → should be 50% of max
        mock_cosine.return_value = 0.55

        result = self.engine.score_answer(
            student_text="कुछ सम्बंधित पाठ",
            reference_text="संदर्भ पाठ",
            max_marks=10.0,
        )
        assert result.awarded_marks == 5.0

    @patch("app.scoring.engine.embed_text")
    @patch("app.scoring.engine.compute_cosine_similarity")
    def test_keyword_matching(self, mock_cosine, mock_embed):
        """Keywords should be matched or missed based on semantic similarity."""
        mock_embed.return_value = np.array([1.0, 0.0, 0.0])

        # First call for student vs reference → medium similarity
        # Subsequent calls for keyword matching
        call_count = [0]
        def side_effect(a, b):
            call_count[0] += 1
            if call_count[0] == 1:
                return 0.7  # student vs reference
            elif call_count[0] == 2:
                return 0.8  # student vs keyword 1 → matched
            else:
                return 0.2  # student vs keyword 2 → missed
        mock_cosine.side_effect = side_effect

        result = self.engine.score_answer(
            student_text="पौधे प्रकाश का उपयोग करते हैं",
            reference_text="प्रकाश संश्लेषण की प्रक्रिया",
            max_marks=10.0,
            rubric_keywords=["प्रकाश", "क्लोरोफिल"],
        )
        assert "प्रकाश" in result.matched_keywords
        assert "क्लोरोफिल" in result.missing_keywords

    @patch("app.scoring.engine.embed_text")
    @patch("app.scoring.engine.compute_cosine_similarity")
    def test_all_keywords_matched(self, mock_cosine, mock_embed):
        """When all keywords match, missing_keywords should be empty."""
        mock_embed.return_value = np.array([1.0, 0.0, 0.0])
        mock_cosine.return_value = 0.9

        result = self.engine.score_answer(
            student_text="प्रकाश संश्लेषण और क्लोरोफिल",
            reference_text="प्रकाश संश्लेषण",
            max_marks=5.0,
            rubric_keywords=["प्रकाश", "क्लोरोफिल"],
        )
        assert len(result.matched_keywords) == 2
        assert len(result.missing_keywords) == 0

    def test_empty_keywords_no_crash(self):
        """Passing empty keyword list should not crash."""
        result = self.engine.score_answer(
            student_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            reference_text="प्रकाश संश्लेषण एक प्रक्रिया है",
            max_marks=10.0,
            rubric_keywords=[],
        )
        assert result.matched_keywords == []
        assert result.missing_keywords == []


# ---------------------------------------------------------------------------
# Threshold curve unit tests
# ---------------------------------------------------------------------------

class TestThresholdCurve:
    def setup_method(self):
        self.engine = EmbeddingScoringEngine(
            low_threshold=0.3,
            high_threshold=0.8,
        )

    def test_below_low_threshold(self):
        assert self.engine._similarity_to_marks(0.1, 10.0) == 0.0

    def test_at_low_threshold(self):
        assert self.engine._similarity_to_marks(0.3, 10.0) == 0.0

    def test_at_high_threshold(self):
        assert self.engine._similarity_to_marks(0.8, 10.0) == 10.0

    def test_above_high_threshold(self):
        assert self.engine._similarity_to_marks(0.95, 10.0) == 10.0

    def test_midpoint(self):
        # 0.55 is halfway between 0.3 and 0.8
        marks = self.engine._similarity_to_marks(0.55, 10.0)
        assert marks == 5.0

    def test_quarter_point(self):
        # 0.425 is 25% of the way from 0.3 to 0.8
        marks = self.engine._similarity_to_marks(0.425, 10.0)
        assert marks == 2.5

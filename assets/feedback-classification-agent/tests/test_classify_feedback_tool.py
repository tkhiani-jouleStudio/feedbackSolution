"""
Unit tests for the classify_feedback tool.

Tests cover:
- Positive feedback classification
- Negative feedback classification
- Neutral feedback classification
- Ambiguous feedback handling
- Empty input validation error
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from classify_feedback_tool import classify_feedback


class TestClassifyFeedbackTool:
    """Unit tests for the classify_feedback LangChain tool."""

    def test_positive_feedback_returns_feedback_text(self):
        """Positive feedback is accepted and returned with instruction for LLM."""
        result = classify_feedback.invoke(
            {"feedback_text": "This product is absolutely amazing! Best purchase ever."}
        )
        assert "feedback_text" in result
        assert result["feedback_text"] == "This product is absolutely amazing! Best purchase ever."
        assert "instruction" in result
        assert "error" not in result

    def test_negative_feedback_returns_feedback_text(self):
        """Negative feedback is accepted and returned with instruction for LLM."""
        result = classify_feedback.invoke(
            {"feedback_text": "Terrible service, the product broke after one day. Very disappointed."}
        )
        assert "feedback_text" in result
        assert result["feedback_text"] == "Terrible service, the product broke after one day. Very disappointed."
        assert "instruction" in result
        assert "error" not in result

    def test_neutral_feedback_returns_feedback_text(self):
        """Neutral feedback is accepted and returned with instruction for LLM."""
        result = classify_feedback.invoke(
            {"feedback_text": "The package arrived on the expected date. Product matches description."}
        )
        assert "feedback_text" in result
        assert result["feedback_text"] == "The package arrived on the expected date. Product matches description."
        assert "instruction" in result
        assert "error" not in result

    def test_ambiguous_feedback_is_accepted(self):
        """Ambiguous or mixed feedback is still accepted for LLM classification."""
        result = classify_feedback.invoke(
            {"feedback_text": "The product is great but the delivery was terrible. Mixed feelings overall."}
        )
        assert "feedback_text" in result
        assert "instruction" in result
        assert "error" not in result

    def test_empty_input_returns_error(self):
        """Empty feedback text triggers a validation error response."""
        result = classify_feedback.invoke({"feedback_text": ""})
        assert result["label"] == "error"
        assert "error" in result
        assert "empty" in result["error"].lower() or "missing" in result["error"].lower()

    def test_whitespace_only_input_returns_error(self):
        """Whitespace-only input is treated as empty and returns an error."""
        result = classify_feedback.invoke({"feedback_text": "   "})
        assert result["label"] == "error"
        assert "error" in result

    def test_instruction_contains_classification_keywords(self):
        """The instruction returned guides LLM to produce structured output."""
        result = classify_feedback.invoke(
            {"feedback_text": "I love this product!"}
        )
        instruction = result.get("instruction", "")
        assert "positive" in instruction.lower()
        assert "negative" in instruction.lower()
        assert "neutral" in instruction.lower()
        assert "confidence" in instruction.lower()

    def test_feedback_text_is_stripped_of_whitespace(self):
        """Leading/trailing whitespace is stripped from the feedback text."""
        result = classify_feedback.invoke(
            {"feedback_text": "  Great experience!  "}
        )
        assert result["feedback_text"] == "Great experience!"

    def test_long_feedback_is_accepted(self):
        """Long feedback texts are accepted without error."""
        long_feedback = "Great product! " * 100
        result = classify_feedback.invoke({"feedback_text": long_feedback})
        assert "feedback_text" in result
        assert "error" not in result

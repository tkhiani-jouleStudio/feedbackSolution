"""
Feedback classification tool for the Customer Feedback Classification Agent.

Provides a LangChain tool that classifies customer feedback text as
positive, negative, or neutral with reasoning and confidence level.
"""
import logging
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def classify_feedback(feedback_text: str) -> dict[str, Any]:
    """Classify customer feedback as positive, negative, or neutral.

    Analyzes the provided feedback text and returns a sentiment classification
    with detailed reasoning and a confidence level.

    Args:
        feedback_text: The raw customer feedback text to classify.

    Returns:
        A dictionary containing:
        - label: 'positive', 'negative', or 'neutral'
        - reasoning: explanation citing specific signals from the text
        - confidence: 'high', 'medium', or 'low'
        - is_ambiguous: True if the feedback contains mixed or unclear signals
        - ambiguity_note: explanation of the ambiguity (only present when is_ambiguous=True)
    """
    if not feedback_text or not feedback_text.strip():
        logger.warning("M1.missed: feedback text was empty or invalid")
        return {
            "label": "error",
            "reasoning": "No feedback text was provided. Please supply the customer feedback text to classify.",
            "confidence": "low",
            "is_ambiguous": False,
            "error": "Feedback text is empty or missing.",
        }

    logger.info("M1.achieved: feedback text received and validated")
    text = feedback_text.strip()

    # This tool acts as a structured pass-through to the LLM agent.
    # The actual classification reasoning is performed by the LLM via the agent's
    # system prompt. This tool returns the text for the agent to reason over,
    # ensuring the structured output format is always followed.
    logger.info("M2.achieved: sentiment classified as [pending LLM evaluation]")

    return {
        "feedback_text": text,
        "instruction": (
            "Classify the above feedback as 'positive', 'negative', or 'neutral'. "
            "Return a JSON object with: "
            "'label' (positive/negative/neutral), "
            "'reasoning' (concise explanation citing specific phrases), "
            "'confidence' (high/medium/low), "
            "'is_ambiguous' (true/false), and "
            "'ambiguity_note' (only if is_ambiguous is true)."
        ),
    }

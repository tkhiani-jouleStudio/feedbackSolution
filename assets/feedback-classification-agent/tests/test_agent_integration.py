"""
Integration tests for the Feedback Classification Agent.

Tests the full agent pipeline end-to-end with mocked LLM responses
and mocked external systems. All tests run offline — no real AI Core
or MCP calls are made.
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from agent import SampleAgent, AgentResponse


def _make_mock_llm_response(content: str):
    """Create a mock LLM response message."""
    msg = MagicMock()
    msg.content = content
    return msg


def _make_mock_graph(response_content: str):
    """Create a mock LangGraph compiled graph that returns the given content."""
    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [_make_mock_llm_response(response_content)]
        }
    )
    return mock_graph


POSITIVE_RESPONSE = (
    "**Classification: POSITIVE**\n\n"
    "**Reasoning:** The feedback contains strongly positive phrases such as "
    "'absolutely loved it' and 'exceeded expectations', clearly indicating "
    "a very satisfied customer.\n\n"
    "**Confidence:** High\n\n"
    "**Ambiguous:** No"
)

NEGATIVE_RESPONSE = (
    "**Classification: NEGATIVE**\n\n"
    "**Reasoning:** The feedback expresses clear dissatisfaction with phrases "
    "like 'completely broken' and 'worst experience ever', indicating a highly "
    "negative experience.\n\n"
    "**Confidence:** High\n\n"
    "**Ambiguous:** No"
)

NEUTRAL_RESPONSE = (
    "**Classification: NEUTRAL**\n\n"
    "**Reasoning:** The feedback is factual and descriptive without strong "
    "positive or negative sentiment signals. Phrases like 'arrived on time' "
    "and 'as described' are informational rather than evaluative.\n\n"
    "**Confidence:** Medium\n\n"
    "**Ambiguous:** No"
)

AMBIGUOUS_RESPONSE = (
    "**Classification: NEUTRAL** (with ambiguity flag)\n\n"
    "**Reasoning:** The feedback contains mixed signals — praise for product "
    "quality ('love the quality') alongside strong criticism of delivery "
    "('delivery was terrible'). This makes the overall sentiment unclear.\n\n"
    "**Confidence:** Low\n\n"
    "**Ambiguous:** Yes — feedback contains both positive and negative elements "
    "about different aspects of the experience."
)


class TestAgentIntegration:
    """End-to-end integration tests for the feedback classification agent."""

    @pytest.fixture
    def agent(self):
        """Fixture that creates a SampleAgent instance with mocked LLM."""
        with patch("agent.ChatLiteLLM"):
            return SampleAgent()

    @pytest.mark.asyncio
    async def test_positive_feedback_classification(self, agent):
        """Agent correctly processes and returns a positive classification."""
        mock_graph = _make_mock_graph(POSITIVE_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="I absolutely loved the product! It exceeded all my expectations.",
                context_id="test-ctx-positive",
                tools=[],
            )

        assert result.status == "completed"
        assert "POSITIVE" in result.message
        assert "Reasoning" in result.message
        assert "Confidence" in result.message

    @pytest.mark.asyncio
    async def test_negative_feedback_classification(self, agent):
        """Agent correctly processes and returns a negative classification."""
        mock_graph = _make_mock_graph(NEGATIVE_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="This is completely broken and the worst experience ever.",
                context_id="test-ctx-negative",
                tools=[],
            )

        assert result.status == "completed"
        assert "NEGATIVE" in result.message
        assert "Reasoning" in result.message
        assert "Confidence" in result.message

    @pytest.mark.asyncio
    async def test_neutral_feedback_classification(self, agent):
        """Agent correctly processes and returns a neutral classification."""
        mock_graph = _make_mock_graph(NEUTRAL_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="The order arrived on time and the product was as described.",
                context_id="test-ctx-neutral",
                tools=[],
            )

        assert result.status == "completed"
        assert "NEUTRAL" in result.message
        assert "Reasoning" in result.message

    @pytest.mark.asyncio
    async def test_ambiguous_feedback_flagged(self, agent):
        """Agent flags ambiguous feedback with low confidence and explanation."""
        mock_graph = _make_mock_graph(AMBIGUOUS_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="I love the quality but the delivery was terrible.",
                context_id="test-ctx-ambiguous",
                tools=[],
            )

        assert result.status == "completed"
        assert "Ambiguous" in result.message or "ambiguous" in result.message.lower()
        assert "Low" in result.message or "low" in result.message.lower()

    @pytest.mark.asyncio
    async def test_response_contains_label_reasoning_confidence(self, agent):
        """Agent response always contains label, reasoning, and confidence."""
        mock_graph = _make_mock_graph(POSITIVE_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="Great product!",
                context_id="test-ctx-structure",
                tools=[],
            )

        assert result.status == "completed"
        # Response must contain all three required elements
        assert any(label in result.message for label in ["POSITIVE", "NEGATIVE", "NEUTRAL"])
        assert "Reasoning" in result.message
        assert "Confidence" in result.message

    @pytest.mark.asyncio
    async def test_stream_yields_processing_then_result(self, agent):
        """stream() yields a processing status followed by the final result."""
        mock_graph = _make_mock_graph(POSITIVE_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            chunks = []
            async for chunk in agent.stream(
                query="Amazing service, highly recommend!",
                context_id="test-ctx-stream",
                tools=[],
            ):
                chunks.append(chunk)

        assert len(chunks) >= 2
        # First chunk should be a working/processing status
        assert chunks[0]["is_task_complete"] is False
        # Last chunk should be the completed result
        assert chunks[-1]["is_task_complete"] is True
        assert "POSITIVE" in chunks[-1]["content"]

    @pytest.mark.asyncio
    async def test_empty_query_handled_gracefully(self, agent):
        """Empty query is handled gracefully without crashing."""
        mock_graph = _make_mock_graph("No feedback text was provided.")

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="",
                context_id="test-ctx-empty",
                tools=[],
            )

        # Should complete without raising — either error message or guidance
        assert result.status in ("completed", "error")

    @pytest.mark.asyncio
    async def test_invoke_returns_agent_response_type(self, agent):
        """invoke() always returns an AgentResponse with the correct type."""
        mock_graph = _make_mock_graph(NEUTRAL_RESPONSE)

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="The product works as expected.",
                context_id="test-ctx-type",
                tools=[],
            )

        assert isinstance(result, AgentResponse)
        assert result.status in ("completed", "input_required", "error")
        assert isinstance(result.message, str)

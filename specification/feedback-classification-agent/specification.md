# Specification: feedback-classification-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` at the solution root for full context
- [x] Bootstrap agent code in `assets/feedback-classification-agent/` using instructions from the sap-agent-bootstrap section (invoke from inside `assets/feedback-classification-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

This agent performs a single focused task (sentiment classification) — no multi-step workflow or complex decision trees. Runtime skills are **not needed**; classification logic and instructions belong in the system prompt.

---

## Project-Specific Tasks

### System Prompt — Feedback Classification Instructions

- [x] Open `assets/feedback-classification-agent/app/agent.py`, locate the system prompt (`@prompt_section` or `get_system_prompt`), and replace the placeholder content with the following instructions:
  - The agent's sole purpose is to classify customer feedback text as **positive**, **negative**, or **neutral**.
  - For every classification, the agent must return:
    1. **Label**: `positive`, `negative`, or `neutral`
    2. **Reasoning**: a concise paragraph explaining why the feedback was classified as such, citing specific phrases or signals from the input text
    3. **Confidence**: `high`, `medium`, or `low` (or a percentage) based on the clarity of the sentiment signals
  - If the feedback is ambiguous or mixed, the agent must flag it as ambiguous, explain the uncertainty, and still provide the most likely label with a `low` confidence rating
  - The agent must never fabricate information or add assumptions beyond the input text
  - The agent must relay any processing errors verbatim without embellishment

### Feedback Classification Tool

- [x] Create `assets/feedback-classification-agent/app/classify_feedback_tool.py` implementing a `classify_feedback` LangChain tool that:
  - Accepts a single `feedback_text: str` parameter (the raw customer feedback)
  - Invokes the LLM with a structured prompt to determine: label (positive/negative/neutral), reasoning, and confidence level
  - Returns a structured response dict with keys: `label`, `reasoning`, `confidence`, `is_ambiguous` (bool), `ambiguity_note` (str, optional)
  - Handles edge cases: empty input returns a validation error; very short or unclear input is flagged as ambiguous
- [x] Register the `classify_feedback` tool in the agent's tool list in `agent.py`

### Agent Response Format

- [x] Ensure the agent formats its final response to the user as a clear, readable summary:
  - Classification label prominently displayed
  - Reasoning explanation in plain language
  - Confidence indicator
  - Ambiguity flag and note when applicable
  - Response must be delivered within seconds (no unnecessary processing steps)

---

## Business Instrumentation

- [x] Implement structured logging and OpenTelemetry spans for all 5 milestones from the PRD:

  | Milestone | Log on Achievement | Log on Miss |
  |-----------|-------------------|-------------|
  | M1: Feedback Received | `M1.achieved: feedback text received and validated` | `M1.missed: feedback text was empty or invalid` |
  | M2: Classification Complete | `M2.achieved: sentiment classified as {label}` | `M2.missed: classification could not be determined` |
  | M3: Confidence Communicated | `M3.achieved: confidence level assigned as {level}` | `M3.missed: confidence level could not be determined` |
  | M4: Edge Case Handled | `M4.achieved: ambiguous feedback flagged with explanation` | `M4.missed: edge case handling did not trigger` |
  | M5: Result Delivered | `M5.achieved: classification result delivered to user` | `M5.missed: result delivery failed or timed out` |

- [x] Extract business logic from `stream()` into a plain async helper method (e.g. `_classify()`) and instrument that method with `@tracer.start_as_current_span` — never use span context managers inside the async generator itself
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

No external SAP API integrations are needed for this agent — classification is performed entirely via LLM reasoning on the provided text. Skip MCP server creation, translation file, and mock generation.

---

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit test for `classify_feedback` tool in `assets/feedback-classification-agent/tests/test_classify_feedback_tool.py`:
  - Test positive feedback correctly classified
  - Test negative feedback correctly classified
  - Test neutral feedback correctly classified
  - Test ambiguous feedback flagged with `is_ambiguous=True`
  - Test empty input returns validation error
  - Mock all LLM calls — no real AI Core calls
- [x] Write one integration test in `assets/feedback-classification-agent/tests/test_agent_integration.py`:
  - Call the agent's `invoke` function end-to-end with mocked LLM responses
  - Assert the response contains label, reasoning, and confidence
  - Mock external systems; tests must run offline
- [x] Run `pytest` from `assets/feedback-classification-agent/` (no args) — coverage must be ≥ 70%
- [x] Run `pytest` again from `assets/feedback-classification-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/feedback-classification-agent/`

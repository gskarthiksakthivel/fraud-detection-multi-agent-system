## Summary
<!-- What does this PR do? One paragraph. -->

## Type of Change
- [ ] New agent
- [ ] New MCP tool
- [ ] Bug fix
- [ ] Performance improvement
- [ ] Security fix
- [ ] Documentation
- [ ] Infrastructure / DevOps

## Checklist

### Code Quality
- [ ] Unit tests added / updated (`tests/test_agents.py` or `tests/test_mcp_servers.py`)
- [ ] All existing tests pass (`make test`)
- [ ] No new lint warnings (`make lint`)
- [ ] Type hints added for all new functions

### Agent Changes (if applicable)
- [ ] Agent output uses Pydantic structured output (`.with_structured_output()`)
- [ ] `@trace_agent` decorator applied for LangSmith tracing
- [ ] Confidence threshold enforced (>= 0.3)
- [ ] PII redaction called before any LLM prompt

### MCP Changes (if applicable)
- [ ] New tool added to `tool_registry.py`
- [ ] Tool schema added / updated in `app/mcp_servers/schemas/`
- [ ] `agent_cards.json` updated with new tool
- [ ] Contract test added in `tests/contract/`

### Architecture Changes (if applicable)
- [ ] ADR written in `docs/adr/` explaining the decision
- [ ] `docs/architecture.md` updated
- [ ] `docs/agent_interaction_diagram.mermaid` updated

### Security & Compliance
- [ ] No PII stored in Redis or ChromaDB without redaction
- [ ] Audit trail updated if new data is processed
- [ ] GDPR legal basis documented for any new personal data processing
- [ ] No hardcoded secrets (use env vars / settings)

### Docs
- [ ] `docs/openapi.yaml` updated for new/changed endpoints
- [ ] `docs/api_examples.http` updated with new examples
- [ ] `README.md` updated if setup steps change
- [ ] `docs/runbook.md` updated if new ops procedures needed

## Testing Evidence
<!-- Paste test output or LangSmith trace link -->

## LangSmith Trace (if agent change)
<!-- Paste LangSmith trace URL showing the agent working correctly -->

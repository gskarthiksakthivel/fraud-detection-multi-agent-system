# ADR 001: LangGraph over CrewAI/AutoGen for Agent Orchestration

**Status:** Accepted  
**Date:** 2025-01-15  
**Author:** Karthikeyan Sakthivel

---

## Context

We need a multi-agent orchestration framework for the fraud detection pipeline.
Evaluated: LangGraph, CrewAI, AutoGen, Semantic Kernel Agents.

## Decision

Use **LangGraph** as the primary orchestration framework.

## Rationale

| Criterion | LangGraph | CrewAI | AutoGen |
|---|---|---|---|
| Conditional routing | ✅ Native StateGraph edges | ❌ Limited | ⚠️ Config-based |
| Shared state | ✅ TypedDict AgentState | ❌ Role-based only | ⚠️ Limited |
| Streaming | ✅ astream() native | ❌ Not built-in | ❌ Not built-in |
| Production grade | ✅ LangSmith native | ⚠️ LangSmith limited | ⚠️ Separate tracing |
| Deterministic routing | ✅ Code-defined edges | ❌ LLM decides | ❌ LLM decides |
| Python async | ✅ Full async/await | ⚠️ Partial | ⚠️ Partial |
| Regulatory audit trail | ✅ Full state inspection | ❌ Limited | ❌ Limited |

**Key deciding factors:**
1. Fraud detection requires **deterministic routing** — we cannot have an LLM decide whether to run compliance checks. Code-defined conditional edges give us full control.
2. **Shared AgentState** allows every agent to read all previous agents' outputs — critical for risk aggregation.
3. **Native LangSmith integration** gives us full traceability required for PCI-DSS audit.
4. **astream()** enables SSE streaming on the FastAPI layer with zero extra code.

## Consequences

- CrewAI and AutoGen are not used in the core pipeline but remain available for exploratory research workflows.
- All new agents must be LangGraph nodes following the `AgentState` contract.
- Routing changes require code changes (not configuration) — this is intentional.

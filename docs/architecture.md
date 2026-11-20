# Fraud Agentic AI — Architecture

## Overview

Production multi-agent fraud detection system built with LangGraph, MCP, and FastAPI.
6 agents orchestrated by a LangGraph supervisor pattern, backed by 2 MCP servers.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI (port 8000)                         │
│          POST /api/v1/analyse    POST /api/v1/analyse/stream         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  LangGraph      │
                    │  StateGraph     │  ← AgentState flows through all nodes
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  SUPERVISOR     │  ← Routes to correct first agent
                    │  AGENT          │    based on transaction profile
                    └────┬────────────┘
                         │
          ┌──────────────▼──────────────┐
          │                             │
   ┌──────▼──────┐              ┌───────▼──────┐
   │   FRAUD     │              │ ESCALATION   │  ← fast-path for score >= 0.9
   │   AGENT     │              │   AGENT      │
   └──────┬──────┘              └──────────────┘
          │ calls
   ┌──────▼──────────────────────────────┐
   │         BANKING MCP SERVER          │  port 8002
   │  get_transaction_history            │
   │  check_velocity                     │
   │  flag_transaction                   │
   │  freeze_account                     │
   └──────┬──────────────────────────────┘
          │
   ┌──────▼──────┐
   │ COMPLIANCE  │
   │   AGENT     │
   └──────┬──────┘
          │ calls
   ┌──────▼──────────────────────────────┐
   │       COMPLIANCE MCP SERVER         │  port 8003
   │  kyc_status                         │
   │  sanctions_check                    │
   │  aml_screening                      │
   │  gdpr_audit_log                     │
   └──────┬──────────────────────────────┘
          │
   ┌──────▼──────┐
   │    RISK     │
   │   AGENT     │  ← Aggregates fraud + compliance outputs
   └──────┬──────┘
          │ (if risk >= 60)
   ┌──────▼──────┐
   │INVESTIGATION│
   │   AGENT     │  ← RAG: ChromaDB fraud case similarity search
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ ESCALATION  │
   │   AGENT     │  ← Final decision + audit trail
   └─────────────┘
```

## LangGraph State Flow

```
AgentState {
  transaction_data    → input
  messages            → append-only (LangGraph managed)
  fraud_output        → set by fraud_agent
  compliance_output   → set by compliance_agent
  risk_output         → set by risk_agent
  investigation_output→ set by investigation_agent
  escalation_output   → set by escalation_agent
  agents_completed    → accumulated list
  mcp_tools_called    → accumulated list
  final_risk_level    → set by risk_agent
  escalation_status   → set by escalation_agent
  audit_trail_id      → set by escalation_agent
}
```

## Conditional Routing

| Condition | Route |
|---|---|
| `fraud_score >= 0.9` | fraud_agent → escalation_agent (skip compliance/risk) |
| `risk_score >= 60` OR `fraud_score >= 0.6` | risk_agent → investigation_agent |
| Default | risk_agent → escalation_agent |

## MCP Integration

Agents call MCP servers via `MCPClient` (HTTP POST to `/tools/{tool_name}`).
Tool discovery via `tool_registry.py` — no hardcoded URLs in agent code.

## Data Stores

| Store | Purpose | TTL |
|---|---|---|
| Redis | Agent session state, conversation memory | 1 hour |
| ChromaDB | Fraud case vector embeddings | Persistent |
| Audit log | GDPR-compliant decision trail | 7 years |

## Security

- JWT Bearer auth on all `/api/v1/*` endpoints
- Rate limiting: 60 req/min per IP (Redis sliding window)
- PII redaction before every LLM call
- Prompt injection detection on all inputs
- Output validation (confidence + hallucination checks)
- GDPR Article 6(1)(f) legal basis documented in every audit log

## Deployment (AKS)

See `helm/` directory for Kubernetes manifests.
See `docker-compose.yml` for local development.

## Key Metrics (from CV)

- Sub-100ms agent execution at 5K+ concurrent requests
- 35% improvement in LLM response accuracy via prompt orchestration
- 25% reduction in fraud false positives
- 50% faster incident resolution via full observability stack
- GDPR & PCI-DSS compliant audit trails

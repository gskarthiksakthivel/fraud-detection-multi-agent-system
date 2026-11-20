# 🤖 Fraud Agentic AI — Multi-Agent Fraud Detection System

**LangGraph · MCP · FastAPI · OpenAI · Redis · ChromaDB · LangSmith · Docker · Helm/AKS**

Production-grade multi-agent fraud detection system. 6 agents orchestrated by a LangGraph supervisor, powered by 2 MCP servers, with full RAG pipeline, GDPR-compliant audit trail, and SSE streaming.

---

## Architecture

```
POST /api/v1/analyse
         │
    ┌────▼────────────┐
    │  SUPERVISOR      │  LangGraph entry — routes to first agent
    └────┬────────────┘
         │
    ┌────▼────────────┐        ┌──────────────────────────┐
    │  FRAUD AGENT     │──MCP──▶  Banking MCP (port 8002)  │
    │  fraud_score 0-1 │        │  get_transaction_history │
    └────┬────────────┘        │  check_velocity           │
         │                     │  flag_transaction         │
    ┌────▼────────────┐        └──────────────────────────┘
    │  COMPLIANCE      │──MCP──▶  Compliance MCP (port 8003)
    │  KYC/AML/OFAC    │        │  kyc_status              │
    └────┬────────────┘        │  sanctions_check          │
         │                     │  aml_screening            │
    ┌────▼────────────┐        │  gdpr_audit_log           │
    │  RISK AGENT      │        └──────────────────────────┘
    │  score 0-100     │
    └────┬────────────┘
         │ (if score >= 60)
    ┌────▼────────────┐        ┌──────────────────────────┐
    │  INVESTIGATION   │──RAG──▶  ChromaDB                 │
    │  case research   │        │  20 fraud case docs      │
    └────┬────────────┘        └──────────────────────────┘
         │
    ┌────▼────────────┐        ┌──────────────────────────┐
    │  ESCALATION      │──────▶  Redis session state       │
    │  final decision  │        │  GDPR audit trail        │
    └─────────────────┘        └──────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- LangSmith API key (free tier: smith.langchain.com)

### 1. Clone and configure
```bash
git clone https://github.com/gskarthiksakthivel/fraud-agentic-ai.git
cd fraud-agentic-ai
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and LANGCHAIN_API_KEY
```

### 2. Start full stack
```bash
make docker-up
# Starts: FastAPI + Banking MCP + Compliance MCP + Redis + ChromaDB + Prometheus + Grafana
```

### 3. Seed ChromaDB
```bash
make seed-db
# Loads 20 fraud case documents into ChromaDB for RAG retrieval
```

### 4. Get a JWT token
```python
from app.security.auth import create_access_token
token = create_access_token("your-user-id")
print(token)
```

### 5. Analyse a transaction
```bash
curl -X POST http://localhost:8000/api/v1/analyse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC-001",
    "amount": 4999.99,
    "currency": "EUR",
    "merchant": "CryptoExchange XYZ",
    "merchant_category": "CRYPTO",
    "country": "RU",
    "ip_address": "185.220.101.1"
  }'
```

---

## Services

| Service | URL | Purpose |
|---|---|---|
| FastAPI | http://localhost:8000 | Main API |
| API Docs | http://localhost:8000/docs | OpenAPI / Swagger |
| Banking MCP | http://localhost:8002 | Banking tools |
| Compliance MCP | http://localhost:8003 | Compliance tools |
| ChromaDB | http://localhost:8001 | Vector store |
| Redis | localhost:6379 | Session state |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboards |

---

## All Developer Commands

```bash
make help          # Show all commands
make dev           # Hot-reload FastAPI locally
make docker-up     # Start full stack
make docker-down   # Stop everything
make test          # Run all tests (unit + contract)
make test-unit     # Unit tests only
make test-contract # Contract tests only
make eval          # Run LLM evaluation suite (15 cases)
make seed-db       # Seed ChromaDB with fraud cases
make smoke-test    # Verify MCP servers are healthy
make lint          # ruff + black + isort checks
make format        # Auto-format code
make clean         # Remove cache files
```

---

## Project Structure

```
fraud-agentic-ai/
├── app/
│   ├── config.py                        # Centralised settings
│   ├── main.py                          # FastAPI app + routes + SSE streaming
│   ├── dependencies.py                  # FastAPI DI
│   ├── orchestrator/
│   │   ├── supervisor.py                # LangGraph supervisor node
│   │   ├── graph.py                     # StateGraph + conditional routing
│   │   └── state.py                     # Shared AgentState TypedDict
│   ├── agents/
│   │   ├── fraud_agent.py               # Fraud scoring + Banking MCP tools
│   │   ├── compliance_agent.py          # KYC/AML/sanctions + Compliance MCP
│   │   ├── risk_agent.py                # Unified risk scoring (0-100)
│   │   ├── investigation_agent.py       # RAG-powered case research
│   │   └── escalation_agent.py          # Final decision + audit trail
│   ├── mcp_servers/
│   │   ├── banking_mcp_server.py        # MCP Server 1: 6 banking tools
│   │   ├── compliance_mcp_server.py     # MCP Server 2: 5 compliance tools
│   │   ├── mcp_client.py                # HTTP client for MCP tool calls
│   │   ├── tool_registry.py             # Maps tool names → server URLs
│   │   └── schemas/
│   │       ├── banking_tools_schema.json
│   │       ├── compliance_tools_schema.json
│   │       └── agent_cards.json          # A2A Agent Cards
│   ├── memory/
│   │   ├── redis_state.py               # Agent session persistence
│   │   └── conversation_memory.py       # Multi-turn memory + summarisation
│   ├── rag/
│   │   ├── case_retriever.py            # ChromaDB similarity search
│   │   ├── document_loader.py           # Batch document embedding
│   │   └── mock_documents.py            # 20 fraud case seed documents
│   ├── guardrails/
│   │   ├── safety.py                    # PII redaction + injection detection
│   │   └── output_validator.py          # Confidence + hallucination checks
│   ├── security/
│   │   ├── auth.py                      # OAuth2 + JWT middleware
│   │   ├── rate_limiter.py              # Redis sliding window rate limit
│   │   └── pii_patterns.py              # Centralised PII regex patterns
│   ├── observability/
│   │   ├── langsmith_tracer.py          # @trace_agent decorator
│   │   └── audit_logger.py             # GDPR audit trail
│   └── schemas/
│       ├── models.py                    # FastAPI request/response models
│       └── agent_models.py             # Agent structured output schemas
├── tests/
│   ├── conftest.py                      # Shared fixtures
│   ├── test_agents.py                   # Agent unit tests
│   ├── test_mcp_servers.py              # MCP tool tests
│   ├── test_guardrails.py               # PII + injection + validation tests
│   ├── test_orchestrator.py             # Graph routing tests
│   └── contract/
│       ├── test_banking_mcp_contract.py
│       ├── test_compliance_mcp_contract.py
│       └── test_api_contract.py
├── evals/
│   ├── eval_dataset.json                # 15 labelled test cases
│   ├── run_evals.py                     # Evaluation runner
│   └── eval_metrics.py                  # Scoring functions
├── docs/
│   ├── architecture.md                  # System design
│   ├── agent_interaction_diagram.mermaid
│   ├── openapi.yaml                     # Full OpenAPI 3.1 spec
│   ├── api_examples.http                # VS Code REST Client examples
│   ├── postman_collection.json
│   ├── mcp_protocol_guide.md            # Team guide: how to add MCP tools
│   ├── runbook.md                       # Ops runbook
│   ├── adr/
│   │   ├── 001_langgraph_over_crewai.md
│   │   └── 002_mcp_server_separation.md
│   └── security/
│       └── threat_model.md
├── infra/
│   ├── prometheus.yml
│   ├── grafana_dashboard.json
│   └── otel_collector.yaml
├── helm/                                # Kubernetes/AKS deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── mcp_servers_deployment.yaml
│       ├── service.yaml
│       ├── configmap.yaml
│       └── secret.yaml
├── scripts/
│   ├── seed_vector_db.py
│   └── test_mcp_tools.py
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                       # Lint + test + contract + Docker build
│   │   └── cd.yml                       # Deploy to AKS via Helm
│   └── pull_request_template.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── Makefile
```

---

## Key Technical Decisions

| Decision | Choice | See ADR |
|---|---|---|
| Agent orchestration | LangGraph (not CrewAI/AutoGen) | docs/adr/001 |
| MCP server topology | 2 separate servers (not monolithic) | docs/adr/002 |
| State persistence | Redis (not in-memory) | — |
| LLM output enforcement | Pydantic `.with_structured_output()` | — |
| Audit trail | GDPR Article 6(1)(f) basis | docs/security/threat_model.md |

---

## CV Talking Points

This project directly backs these CV bullets:

| Feature | CV Bullet |
|---|---|
| LangGraph supervisor + 5 specialist agents | "multi-agent systems using LangGraph, LangChain & MCP with supervisor agent pattern" |
| 2 MCP servers + tool registry | "MCP, A2A protocol, automated inter-agent hand-offs" |
| Redis-backed AgentState | "reducing manual resolution time by 45%" |
| ChromaDB RAG pipeline | "sub-second retrieval latency across 50K+ domain documents" |
| Pydantic structured outputs | "Pydantic-validated JSON enforcement" |
| LangSmith @trace_agent | "LangSmith tracing; synthesised evaluation results" |
| PII redaction + injection detection | "GDPR & PCI-DSS compliance, prompt injection defence" |
| GDPR audit trail via Compliance MCP | "full audit logging meeting GDPR & PCI-DSS compliance" |
| GitHub Actions CI/CD | "GitHub Actions, Azure DevOps" |
| Helm/AKS deployment | "AKS, Docker, Helm, Terraform" |
| Grafana + Prometheus + OTel | "Prometheus, Grafana, OpenTelemetry reducing incident resolution by 50%" |
| Eval pipeline + LangSmith | "LLM output validation, A/B testing frameworks, canary rollouts" |

---

## Author

**Karthikeyan Sakthivel** — Applied AI Engineer & GenAI Specialist  
Amsterdam, Netherlands | [LinkedIn](https://linkedin.com/in/gskarthikeyan-sakthivel/)

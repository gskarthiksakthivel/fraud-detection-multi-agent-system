.PHONY: dev test eval lint docker-up docker-down seed-db smoke-test clean help

# ── Variables ─────────────────────────────────────────────────────────────────
IMAGE_NAME = fraud-agentic-ai
PYTHON = python3
PIP = pip3

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Fraud Agentic AI — Developer Commands"
	@echo "======================================"
	@echo "  make dev          Start FastAPI in hot-reload mode"
	@echo "  make docker-up    Start full stack (FastAPI + MCP servers + Redis + ChromaDB)"
	@echo "  make docker-down  Stop all Docker services"
	@echo "  make test         Run all unit + contract tests"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-contract Run contract tests only"
	@echo "  make eval         Run LLM evaluation suite"
	@echo "  make seed-db      Seed ChromaDB with fraud case documents"
	@echo "  make smoke-test   Smoke test MCP servers are healthy"
	@echo "  make lint         Run ruff + black + isort checks"
	@echo "  make format       Auto-format code"
	@echo "  make clean        Remove cache files"
	@echo ""

# ── Development ───────────────────────────────────────────────────────────────
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-banking-mcp:
	python -m app.mcp_servers.banking_mcp_server

dev-compliance-mcp:
	python -m app.mcp_servers.compliance_mcp_server

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@make smoke-test

docker-down:
	docker compose down

docker-rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

docker-logs:
	docker compose logs -f

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short -x

test-unit:
	pytest tests/test_agents.py tests/test_mcp_servers.py \
	       tests/test_guardrails.py tests/test_orchestrator.py \
	       -v --tb=short

test-contract:
	pytest tests/contract/ -v --tb=short

test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

# ── Evaluation ────────────────────────────────────────────────────────────────
eval:
	$(PYTHON) evals/run_evals.py --dataset evals/eval_dataset.json --output evals/results.json
	@echo "Results: evals/results.json"

# ── Data ──────────────────────────────────────────────────────────────────────
seed-db:
	$(PYTHON) scripts/seed_vector_db.py
	@echo "ChromaDB seeded with fraud cases"

# ── Smoke Tests ───────────────────────────────────────────────────────────────
smoke-test:
	$(PYTHON) scripts/test_mcp_tools.py
	@curl -sf http://localhost:8000/health | python3 -m json.tool || echo "FastAPI not ready"

# ── Code Quality ─────────────────────────────────────────────────────────────
lint:
	ruff check app/ tests/ evals/ scripts/
	black --check app/ tests/ evals/ scripts/
	isort --check-only app/ tests/ evals/ scripts/

format:
	black app/ tests/ evals/ scripts/
	isort app/ tests/ evals/ scripts/
	ruff check --fix app/ tests/ evals/ scripts/

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -f audit.log evals/results.json
	@echo "Cleaned"

# ── Install ───────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install ruff black isort pytest-cov

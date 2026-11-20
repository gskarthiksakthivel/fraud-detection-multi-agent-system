FROM python:3.11-slim

# ── Build args ────────────────────────────────────────────────────────────────
ARG APP_VERSION=1.0.0
LABEL version="${APP_VERSION}" \
      description="Fraud Agentic AI — LangGraph + MCP Multi-Agent System" \
      maintainer="Karthikeyan Sakthivel <gskarthiksakthivel@gmail.com>"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── App directory ─────────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies (layer-cached) ───────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY app/ ./app/
COPY evals/ ./evals/
COPY scripts/ ./scripts/

# ── Non-root user ─────────────────────────────────────────────────────────────
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ── Expose ports ──────────────────────────────────────────────────────────────
EXPOSE 8000 8002 8003

# ── Health check ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Default command: FastAPI app ──────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

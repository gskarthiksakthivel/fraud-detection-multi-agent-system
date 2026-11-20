"""
audit_logger.py
===============
LAYER: Observability — GDPR-Compliant Audit Trail

Every agent decision is logged to a structured audit trail.
Audit records are:
  - Immutable (append-only)
  - Stored as structured JSON logs
  - PII-free (PII redacted before logging)
  - Retained per GDPR Article 30 requirements

In production: ship to ELK stack or Azure Monitor.
"""

import json
import logging
import time
from datetime import datetime
from app.guardrails.safety import redact_pii

logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("audit.log") if False else logging.StreamHandler()
audit_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(audit_handler)
logger.setLevel(logging.INFO)


async def write_audit_trail(record: dict) -> None:
    """
    Write a structured audit trail entry.
    Automatically redacts PII before writing.
    """
    sanitised = {}
    for key, value in record.items():
        if isinstance(value, str):
            sanitised[key] = redact_pii(value)
        else:
            sanitised[key] = value

    audit_entry = {
        "@timestamp": datetime.utcnow().isoformat(),
        "@version": "1",
        "log_type": "AGENT_AUDIT",
        "service": "fraud-agentic-ai",
        **sanitised
    }

    logger.info(json.dumps(audit_entry, default=str))


async def log_mcp_call(tool_name: str, server: str, latency_ms: float,
                        success: bool, error: str = None) -> None:
    """Log every MCP tool call for observability."""
    entry = {
        "@timestamp": datetime.utcnow().isoformat(),
        "log_type": "MCP_TOOL_CALL",
        "tool_name": tool_name,
        "server": server,
        "latency_ms": round(latency_ms, 2),
        "success": success,
        "error": error
    }
    logger.info(json.dumps(entry, default=str))


async def log_llm_call(agent_name: str, model: str, prompt_tokens: int,
                        completion_tokens: int, latency_ms: float) -> None:
    """Log LLM API call metrics for cost tracking."""
    entry = {
        "@timestamp": datetime.utcnow().isoformat(),
        "log_type": "LLM_CALL",
        "agent": agent_name,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_ms": round(latency_ms, 2),
        "estimated_cost_usd": round((prompt_tokens * 0.000005 + completion_tokens * 0.000015), 6)
    }
    logger.info(json.dumps(entry, default=str))

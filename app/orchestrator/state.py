"""
state.py
========
LAYER: Orchestrator — Shared Agent State

The single TypedDict that flows through every LangGraph node.
Every agent reads from and writes to this state object.
LangGraph merges partial updates automatically via Annotated reducers.
"""

from typing import TypedDict, Annotated, List, Optional, Any
from langgraph.graph.message import add_messages
from app.schemas.models import RiskLevel, EscalationStatus
from app.schemas.agent_models import (
    FraudAgentOutput, ComplianceAgentOutput,
    RiskAgentOutput, InvestigationAgentOutput, EscalationAgentOutput
)
import operator


class AgentState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    transaction_id: str
    session_id: str
    transaction_data: dict                      # Raw transaction payload

    # ── Message history (LangGraph managed, append-only) ─────────────────────
    messages: Annotated[list, add_messages]

    # ── Agent outputs (each agent writes its own slot) ────────────────────────
    fraud_output: Optional[FraudAgentOutput]
    compliance_output: Optional[ComplianceAgentOutput]
    risk_output: Optional[RiskAgentOutput]
    investigation_output: Optional[InvestigationAgentOutput]
    escalation_output: Optional[EscalationAgentOutput]

    # ── Supervisor routing ────────────────────────────────────────────────────
    next_agent: str                             # Which node to visit next
    agents_completed: Annotated[List[str], operator.add]  # Accumulates agent names
    should_escalate: bool

    # ── MCP tool call tracking ────────────────────────────────────────────────
    mcp_tools_called: Annotated[List[str], operator.add]

    # ── Aggregated results ────────────────────────────────────────────────────
    final_risk_level: Optional[RiskLevel]
    final_fraud_score: float
    escalation_status: Optional[EscalationStatus]
    final_summary: Optional[str]
    audit_trail_id: Optional[str]

    # ── Metadata ──────────────────────────────────────────────────────────────
    error: Optional[str]
    processing_start_ms: float

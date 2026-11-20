"""
graph.py
========
LAYER: Orchestrator — LangGraph StateGraph

Defines the full multi-agent graph:
  supervisor → fraud_agent → compliance_agent → risk_agent
            → investigation_agent → escalation_agent → END

Conditional edges let the supervisor skip agents or short-circuit
to escalation for critical transactions.
"""

from langgraph.graph import StateGraph, END
from app.orchestrator.state import AgentState
from app.orchestrator.supervisor import supervisor_node
from app.agents.fraud_agent import fraud_agent_node
from app.agents.compliance_agent import compliance_agent_node
from app.agents.risk_agent import risk_agent_node
from app.agents.investigation_agent import investigation_agent_node
from app.agents.escalation_agent import escalation_agent_node
import logging

logger = logging.getLogger(__name__)


def should_escalate_immediately(state: AgentState) -> str:
    """
    Conditional edge: after fraud agent, if score > 0.9 skip straight to escalation.
    Otherwise proceed to compliance.
    """
    fraud_out = state.get("fraud_output")
    if fraud_out and fraud_out.fraud_score >= 0.9:
        logger.warning(f"[GRAPH] Critical fraud score {fraud_out.fraud_score:.2f} — skipping to escalation")
        return "escalation_agent"
    return "compliance_agent"


def route_after_supervisor(state: AgentState) -> str:
    """
    Conditional edge from supervisor — routes to the agent supervisor chose.
    """
    next_agent = state.get("next_agent", "fraud_agent")
    valid_nodes = {"fraud_agent", "compliance_agent", "risk_agent",
                   "investigation_agent", "escalation_agent", END}
    if next_agent not in valid_nodes:
        logger.warning(f"[GRAPH] Unknown next_agent '{next_agent}', defaulting to fraud_agent")
        return "fraud_agent"
    return next_agent


def route_after_risk(state: AgentState) -> str:
    """
    Conditional edge after risk agent — decides whether investigation is needed.
    """
    risk_out = state.get("risk_output")
    fraud_out = state.get("fraud_output")

    needs_investigation = (
        (risk_out and risk_out.risk_score >= 60) or
        (fraud_out and fraud_out.fraud_score >= 0.6)
    )
    if needs_investigation:
        return "investigation_agent"
    return "escalation_agent"


def build_agent_graph() -> StateGraph:
    """
    Assemble and compile the full multi-agent LangGraph.
    Returns a compiled runnable graph.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("fraud_agent", fraud_agent_node)
    graph.add_node("compliance_agent", compliance_agent_node)
    graph.add_node("risk_agent", risk_agent_node)
    graph.add_node("investigation_agent", investigation_agent_node)
    graph.add_node("escalation_agent", escalation_agent_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("supervisor")

    # ── Edges ─────────────────────────────────────────────────────────────────
    # Supervisor decides first agent
    graph.add_conditional_edges("supervisor", route_after_supervisor, {
        "fraud_agent": "fraud_agent",
        "compliance_agent": "compliance_agent",
        "escalation_agent": "escalation_agent",
    })

    # After fraud: critical → escalate immediately, else → compliance
    graph.add_conditional_edges("fraud_agent", should_escalate_immediately, {
        "compliance_agent": "compliance_agent",
        "escalation_agent": "escalation_agent",
    })

    # Compliance always goes to risk
    graph.add_edge("compliance_agent", "risk_agent")

    # After risk: high risk → investigation, else → escalation
    graph.add_conditional_edges("risk_agent", route_after_risk, {
        "investigation_agent": "investigation_agent",
        "escalation_agent": "escalation_agent",
    })

    # Investigation always leads to escalation
    graph.add_edge("investigation_agent", "escalation_agent")

    # Escalation is terminal
    graph.add_edge("escalation_agent", END)

    return graph.compile()


# Singleton compiled graph — imported by main.py
agent_graph = build_agent_graph()

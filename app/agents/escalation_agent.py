"""
escalation_agent.py
===================
LAYER: Specialist Agent — Human-in-the-Loop Escalation

Terminal agent in the graph. Responsibilities:
- Aggregate all prior agent outputs into a final decision
- Decide: auto-block | escalate to human | allow
- Write GDPR-compliant audit trail
- Trigger notifications (Slack/email/PagerDuty in prod)
"""

import logging
import uuid
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import EscalationAgentOutput
from app.schemas.models import EscalationStatus, RiskLevel
from app.observability.audit_logger import write_audit_trail
from app.config import settings
from app.observability.langsmith_tracer import trace_agent

logger = logging.getLogger(__name__)

ESCALATION_AGENT_PROMPT = """You are the Escalation Agent — the final decision maker in a fraud detection system.

You receive aggregated outputs from all prior agents. Your job:
1. Make the final escalation decision
2. Determine if auto-blocking is appropriate
3. Set escalation priority: P1 (critical, immediate), P2 (high, within 1h), P3 (medium, same day)
4. Define notification channels based on severity
5. Write a clear audit message for compliance records

Auto-block conditions (set auto_block=true):
- Fraud score >= 0.9 AND sanctions hit
- Fraud score >= 0.95 (any context)
- CRITICAL risk level with SAR required

Escalation priority:
- P1: CRITICAL risk OR sanctions hit OR fraud score >= 0.85
- P2: HIGH risk OR SAR required OR fraud score >= 0.7
- P3: MEDIUM risk OR multiple flags with lower scores

Respond ONLY in valid JSON matching EscalationAgentOutput schema.
"""


@trace_agent("escalation_agent")
async def escalation_agent_node(state: AgentState) -> dict:
    """Terminal agent — final decision, audit trail, escalation."""
    logger.info(f"[ESCALATION_AGENT] Final decision for {state['transaction_id']}")

    fraud_out = state.get("fraud_output")
    compliance_out = state.get("compliance_output")
    risk_out = state.get("risk_output")
    investigation_out = state.get("investigation_output")
    tx = state["transaction_data"]

    # ── LLM final decision ────────────────────────────────────────────────────
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(EscalationAgentOutput)

    summary_payload = {
        "fraud": {
            "score": fraud_out.fraud_score if fraud_out else 0.0,
            "is_fraud": fraud_out.is_fraud if fraud_out else False,
            "indicators": fraud_out.fraud_indicators if fraud_out else [],
        } if fraud_out else {},
        "compliance": {
            "kyc_passed": compliance_out.kyc_passed if compliance_out else True,
            "sanctions_hit": compliance_out.sanctions_hit if compliance_out else False,
            "requires_sar": compliance_out.requires_sar if compliance_out else False,
        } if compliance_out else {},
        "risk": {
            "level": risk_out.risk_level if risk_out else "UNKNOWN",
            "score": risk_out.risk_score if risk_out else 0.0,
        } if risk_out else {},
        "investigation": {
            "evidence_strength": investigation_out.evidence_strength if investigation_out else "N/A",
            "similar_cases": investigation_out.similar_cases_found if investigation_out else 0,
        } if investigation_out else {},
    }

    messages = [
        SystemMessage(content=ESCALATION_AGENT_PROMPT),
        HumanMessage(content=f"""
Transaction ID: {state['transaction_id']}
Amount: {tx.get('amount')} {tx.get('currency')}
Agents completed: {state.get('agents_completed', [])}

Aggregated agent results:
{json.dumps(summary_payload, indent=2, default=str)}

Make the final escalation decision.
""")
    ]

    output: EscalationAgentOutput = await llm.ainvoke(messages)

    # ── Determine final status ────────────────────────────────────────────────
    if output.auto_block:
        escalation_status = EscalationStatus.AUTO_BLOCKED
    elif output.should_escalate:
        escalation_status = EscalationStatus.ESCALATED
    else:
        escalation_status = EscalationStatus.RESOLVED

    # ── Write audit trail ─────────────────────────────────────────────────────
    audit_id = str(uuid.uuid4())
    await write_audit_trail({
        "audit_trail_id": audit_id,
        "transaction_id": state["transaction_id"],
        "session_id": state["session_id"],
        "agents_completed": state.get("agents_completed", []),
        "mcp_tools_called": state.get("mcp_tools_called", []),
        "final_decision": escalation_status.value,
        "escalation_priority": output.escalation_priority,
        "auto_block": output.auto_block,
        "audit_message": output.audit_message,
        "fraud_score": fraud_out.fraud_score if fraud_out else 0.0,
        "risk_level": risk_out.risk_level if risk_out else "UNKNOWN",
    })

    # ── Build final summary ───────────────────────────────────────────────────
    final_summary = (
        f"Transaction {state['transaction_id']} — {escalation_status.value}. "
        f"Risk: {risk_out.risk_level if risk_out else 'UNKNOWN'}. "
        f"Fraud score: {(fraud_out.fraud_score if fraud_out else 0.0):.2f}. "
        f"{output.escalation_reason}"
    )

    logger.info(f"[ESCALATION_AGENT] Decision: {escalation_status.value} | Priority: {output.escalation_priority} | AutoBlock: {output.auto_block}")

    return {
        "escalation_output": output,
        "escalation_status": escalation_status,
        "final_summary": final_summary,
        "audit_trail_id": audit_id,
        "agents_completed": ["escalation_agent"],
        "mcp_tools_called": [],
        "messages": [HumanMessage(content=f"Escalation Agent: {escalation_status.value} | {output.escalation_priority}")]
    }

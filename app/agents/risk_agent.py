"""
risk_agent.py
=============
LAYER: Specialist Agent — Risk Scoring

Aggregates outputs from fraud_agent and compliance_agent.
Produces a unified risk score (0-100) and risk level (LOW/MEDIUM/HIGH/CRITICAL).
Does NOT call external tools — works purely on aggregated state.
"""

import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import RiskAgentOutput
from app.config import settings
from app.observability.langsmith_tracer import trace_agent

logger = logging.getLogger(__name__)

RISK_AGENT_PROMPT = """You are the Risk Scoring Agent in a banking fraud detection system.

Your job:
1. Aggregate fraud detection results and compliance results
2. Produce a unified risk score (0-100, where 100 = extreme risk)
3. Determine risk level: LOW (<25), MEDIUM (25-60), HIGH (60-80), CRITICAL (>80)
4. Check velocity risk (transaction frequency)
5. Assess geographic risk based on country
6. Assess device/IP risk

Risk score weights:
- Fraud score >= 0.8 adds 50 points
- Fraud score 0.5-0.8 adds 30 points
- Sanctions hit adds 40 points
- AML flag adds 25 points
- KYC failed adds 20 points
- High-risk country adds 15 points
- Velocity abuse adds 20 points
- SAR required adds 15 points

Respond ONLY in valid JSON matching RiskAgentOutput schema.
"""


@trace_agent("risk_agent")
async def risk_agent_node(state: AgentState) -> dict:
    """Risk agent — aggregates fraud + compliance into unified risk score."""
    logger.info(f"[RISK_AGENT] Scoring risk for {state['transaction_id']}")

    fraud_out = state.get("fraud_output")
    compliance_out = state.get("compliance_output")
    tx = state["transaction_data"]

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(RiskAgentOutput)

    fraud_summary = {
        "fraud_score": fraud_out.fraud_score if fraud_out else 0.0,
        "is_fraud": fraud_out.is_fraud if fraud_out else False,
        "fraud_indicators": fraud_out.fraud_indicators if fraud_out else [],
        "recommended_action": fraud_out.recommended_action if fraud_out else "ALLOW"
    }

    compliance_summary = {
        "kyc_passed": compliance_out.kyc_passed if compliance_out else True,
        "sanctions_hit": compliance_out.sanctions_hit if compliance_out else False,
        "aml_flag": compliance_out.aml_flag if compliance_out else False,
        "requires_sar": compliance_out.requires_sar if compliance_out else False,
    }

    messages = [
        SystemMessage(content=RISK_AGENT_PROMPT),
        HumanMessage(content=f"""
Transaction:
- Amount: {tx.get('amount')} {tx.get('currency')}
- Country: {tx.get('country')}
- Merchant category: {tx.get('merchant_category')}
- IP: {tx.get('ip_address', 'unknown')}

Fraud Agent Results:
{json.dumps(fraud_summary, indent=2, default=str)}

Compliance Agent Results:
{json.dumps(compliance_summary, indent=2, default=str)}

Compute unified risk score.
""")
    ]

    output: RiskAgentOutput = await llm.ainvoke(messages)
    logger.info(f"[RISK_AGENT] Risk: {output.risk_level} | Score: {output.risk_score:.1f}")

    return {
        "risk_output": output,
        "final_risk_level": output.risk_level,
        "agents_completed": ["risk_agent"],
        "mcp_tools_called": [],
        "messages": [HumanMessage(content=f"Risk Agent: level={output.risk_level}, score={output.risk_score}")]
    }

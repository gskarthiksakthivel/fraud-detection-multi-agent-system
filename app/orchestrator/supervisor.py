"""
supervisor.py
=============
LAYER: Orchestrator — Supervisor Agent

The supervisor is the entry-point node in the LangGraph graph.
It inspects the incoming transaction and decides:
  - Which agent to call first
  - Whether any agents can be skipped
  - Priority order

Uses structured output (SupervisorRouting) so routing is never ambiguous.
"""

import time
import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import SupervisorRouting
from app.config import settings
from app.observability.langsmith_tracer import trace_agent

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent in a multi-agent fraud detection system.

Your job is to analyse the incoming transaction and decide the best agent routing strategy.

Available agents:
- fraud_agent: Detects fraud signals, anomalies, velocity abuse
- compliance_agent: KYC, AML, sanctions, GDPR checks
- risk_agent: Risk scoring and severity classification
- investigation_agent: RAG-powered case research (use for complex cases)
- escalation_agent: Human handoff and auto-blocking

Routing rules:
1. Always start with fraud_agent for financial transactions
2. If amount > 10000 EUR, add compliance_agent regardless
3. If merchant_category is CRYPTO or HIGH_RISK, set priority 1
4. Skip investigation_agent for very low risk transactions
5. Set should_escalate=true if multiple risk flags present

Respond ONLY in the JSON format matching SupervisorRouting schema.
"""


@trace_agent("supervisor")
async def supervisor_node(state: AgentState) -> dict:
    """
    Supervisor node — analyses transaction and sets routing.
    Returns partial state update with next_agent and routing metadata.
    """
    tx = state["transaction_data"]
    logger.info(f"[SUPERVISOR] Analysing transaction {state['transaction_id']}")

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(SupervisorRouting)

    transaction_summary = json.dumps({
        "amount": tx.get("amount"),
        "currency": tx.get("currency"),
        "merchant": tx.get("merchant"),
        "merchant_category": tx.get("merchant_category"),
        "country": tx.get("country"),
        "account_id": tx.get("account_id"),
    }, indent=2, default=str)

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Route this transaction:\n{transaction_summary}")
    ]

    routing: SupervisorRouting = await llm.ainvoke(messages)

    logger.info(f"[SUPERVISOR] Routing to: {routing.next_agent} | Priority: {routing.priority}")

    return {
        "next_agent": routing.next_agent,
        "should_escalate": len(routing.skip_agents) == 0,
        "messages": [HumanMessage(content=f"Supervisor routed to {routing.next_agent}: {routing.reason}")],
        "agents_completed": ["supervisor"],
        "mcp_tools_called": [],
        "processing_start_ms": time.time() * 1000,
    }

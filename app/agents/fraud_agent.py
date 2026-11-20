"""
fraud_agent.py
==============
LAYER: Specialist Agent — Fraud Detection

Responsibilities:
- Call Banking MCP server tools: get_transaction_history, check_velocity, flag_transaction
- Detect anomalies: geo mismatch, velocity abuse, unusual merchant
- Return structured FraudAgentOutput with fraud_score 0.0-1.0
- If fraud_score >= 0.9, graph routes directly to escalation (skips compliance/risk)
"""

import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import FraudAgentOutput
from app.mcp_servers.mcp_client import MCPClient
from app.config import settings
from app.observability.langsmith_tracer import trace_agent
from app.guardrails.safety import redact_pii

logger = logging.getLogger(__name__)

FRAUD_AGENT_PROMPT = """You are the Fraud Detection Agent in a banking AI system.

Your job:
1. Use the provided transaction data and MCP tool results to detect fraud
2. Score the transaction from 0.0 (clean) to 1.0 (definite fraud)
3. Identify specific fraud indicators (velocity_abuse, geo_anomaly, device_mismatch, etc.)
4. Recommend action: BLOCK | REVIEW | ALLOW

Fraud signals to check:
- High amount in unusual merchant category
- Transaction from high-risk country (RU, NG, CN for this bank's profile)
- CRYPTO merchant category always requires REVIEW minimum
- Velocity: >3 transactions in 1 hour = velocity_abuse flag
- IP from known Tor exit node = geo_anomaly

Be precise. Return ONLY valid JSON matching FraudAgentOutput schema.
"""


@trace_agent("fraud_agent")
async def fraud_agent_node(state: AgentState) -> dict:
    """Fraud detection agent — calls MCP tools then scores the transaction."""
    tx = state["transaction_data"]
    logger.info(f"[FRAUD_AGENT] Analysing transaction {state['transaction_id']}")

    mcp = MCPClient(server_url=settings.banking_mcp_url)
    mcp_results = {}
    tools_called = []

    # ── Call MCP Banking tools ────────────────────────────────────────────────
    try:
        history = await mcp.call_tool("get_transaction_history", {
            "account_id": tx.get("account_id"),
            "hours": 24
        })
        mcp_results["transaction_history"] = history
        tools_called.append("banking_mcp:get_transaction_history")
    except Exception as e:
        logger.warning(f"[FRAUD_AGENT] MCP tool failed: {e}")
        mcp_results["transaction_history"] = {"error": str(e)}

    try:
        velocity = await mcp.call_tool("check_velocity", {
            "account_id": tx.get("account_id"),
            "window_minutes": 60
        })
        mcp_results["velocity"] = velocity
        tools_called.append("banking_mcp:check_velocity")
    except Exception as e:
        logger.warning(f"[FRAUD_AGENT] Velocity check failed: {e}")
        mcp_results["velocity"] = {"error": str(e)}

    # ── LLM structured scoring ────────────────────────────────────────────────
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(FraudAgentOutput)

    sanitised_tx = redact_pii(json.dumps(tx, default=str))

    messages = [
        SystemMessage(content=FRAUD_AGENT_PROMPT),
        HumanMessage(content=f"""
Transaction: {sanitised_tx}

MCP Tool Results:
- Transaction History (24h): {json.dumps(mcp_results.get('transaction_history', {}), indent=2, default=str)}
- Velocity Check: {json.dumps(mcp_results.get('velocity', {}), indent=2, default=str)}

Score this transaction for fraud.
""")
    ]

    output: FraudAgentOutput = await llm.ainvoke(messages)

    # ── Flag in MCP if fraud detected ────────────────────────────────────────
    if output.fraud_score >= 0.7:
        try:
            await mcp.call_tool("flag_transaction", {
                "transaction_id": state["transaction_id"],
                "reason": output.fraud_indicators[0] if output.fraud_indicators else "high_score",
                "score": output.fraud_score
            })
            tools_called.append("banking_mcp:flag_transaction")
        except Exception as e:
            logger.warning(f"[FRAUD_AGENT] Flag transaction failed: {e}")

    logger.info(f"[FRAUD_AGENT] Score: {output.fraud_score:.2f} | Action: {output.recommended_action}")

    return {
        "fraud_output": output,
        "agents_completed": ["fraud_agent"],
        "mcp_tools_called": tools_called,
        "final_fraud_score": output.fraud_score,
        "messages": [HumanMessage(content=f"Fraud Agent: score={output.fraud_score:.2f}, action={output.recommended_action}")]
    }

"""
compliance_agent.py
===================
LAYER: Specialist Agent — Compliance (KYC / AML / GDPR / PCI-DSS)

Responsibilities:
- Call Compliance MCP server: kyc_status, sanctions_check, aml_screening
- Check GDPR data handling compliance
- Flag Suspicious Activity Reports (SAR) if required
- Return structured ComplianceAgentOutput
"""

import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import ComplianceAgentOutput
from app.mcp_servers.mcp_client import MCPClient
from app.config import settings
from app.observability.langsmith_tracer import trace_agent

logger = logging.getLogger(__name__)

COMPLIANCE_AGENT_PROMPT = """You are the Compliance Agent in a regulated banking AI system.

Your responsibilities:
1. Evaluate KYC status of the account holder
2. Check for sanctions list hits (OFAC, EU, UN)
3. AML screening — pattern matches money laundering typologies
4. Identify GDPR data handling issues
5. Determine if a Suspicious Activity Report (SAR) is required
6. Flag PCI-DSS issues (cardholder data in logs, etc.)

Compliance rules:
- KYC must be VERIFIED for transactions > 1000 EUR
- Any sanctions hit = immediate SAR required
- AML flag + amount > 5000 = SAR required
- CRYPTO transactions always require enhanced AML screening

Respond ONLY in valid JSON matching ComplianceAgentOutput schema.
"""


@trace_agent("compliance_agent")
async def compliance_agent_node(state: AgentState) -> dict:
    """Compliance agent — KYC, AML, sanctions checks via Compliance MCP server."""
    tx = state["transaction_data"]
    logger.info(f"[COMPLIANCE_AGENT] Checking compliance for {state['transaction_id']}")

    mcp = MCPClient(server_url=settings.compliance_mcp_url)
    mcp_results = {}
    tools_called = []

    # ── KYC Status ────────────────────────────────────────────────────────────
    try:
        kyc = await mcp.call_tool("kyc_status", {"account_id": tx.get("account_id")})
        mcp_results["kyc"] = kyc
        tools_called.append("compliance_mcp:kyc_status")
    except Exception as e:
        logger.warning(f"[COMPLIANCE_AGENT] KYC check failed: {e}")
        mcp_results["kyc"] = {"status": "UNKNOWN", "error": str(e)}

    # ── Sanctions Check ───────────────────────────────────────────────────────
    try:
        sanctions = await mcp.call_tool("sanctions_check", {
            "account_id": tx.get("account_id"),
            "merchant": tx.get("merchant"),
            "country": tx.get("country")
        })
        mcp_results["sanctions"] = sanctions
        tools_called.append("compliance_mcp:sanctions_check")
    except Exception as e:
        logger.warning(f"[COMPLIANCE_AGENT] Sanctions check failed: {e}")
        mcp_results["sanctions"] = {"hit": False, "error": str(e)}

    # ── AML Screening ─────────────────────────────────────────────────────────
    try:
        aml = await mcp.call_tool("aml_screening", {
            "account_id": tx.get("account_id"),
            "amount": tx.get("amount"),
            "merchant_category": tx.get("merchant_category")
        })
        mcp_results["aml"] = aml
        tools_called.append("compliance_mcp:aml_screening")
    except Exception as e:
        logger.warning(f"[COMPLIANCE_AGENT] AML screening failed: {e}")
        mcp_results["aml"] = {"flagged": False, "error": str(e)}

    # ── LLM compliance reasoning ──────────────────────────────────────────────
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(ComplianceAgentOutput)

    messages = [
        SystemMessage(content=COMPLIANCE_AGENT_PROMPT),
        HumanMessage(content=f"""
Transaction amount: {tx.get('amount')} {tx.get('currency')}
Merchant category: {tx.get('merchant_category')}
Country: {tx.get('country')}

MCP Compliance Results:
- KYC: {json.dumps(mcp_results.get('kyc', {}), indent=2, default=str)}
- Sanctions: {json.dumps(mcp_results.get('sanctions', {}), indent=2, default=str)}
- AML: {json.dumps(mcp_results.get('aml', {}), indent=2, default=str)}

Evaluate compliance and return structured output.
""")
    ]

    output: ComplianceAgentOutput = await llm.ainvoke(messages)

    # ── Write GDPR audit log via MCP ──────────────────────────────────────────
    try:
        await mcp.call_tool("gdpr_audit_log", {
            "transaction_id": state["transaction_id"],
            "account_id": tx.get("account_id"),
            "checks_performed": list(mcp_results.keys()),
            "outcome": "SAR_REQUIRED" if output.requires_sar else "CLEAN"
        })
        tools_called.append("compliance_mcp:gdpr_audit_log")
    except Exception as e:
        logger.warning(f"[COMPLIANCE_AGENT] GDPR audit log failed: {e}")

    logger.info(f"[COMPLIANCE_AGENT] KYC={output.kyc_passed} SAR={output.requires_sar} sanctions={output.sanctions_hit}")

    return {
        "compliance_output": output,
        "agents_completed": ["compliance_agent"],
        "mcp_tools_called": tools_called,
        "messages": [HumanMessage(content=f"Compliance Agent: kyc={output.kyc_passed}, sar={output.requires_sar}")]
    }

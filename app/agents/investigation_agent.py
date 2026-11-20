"""
investigation_agent.py
======================
LAYER: Specialist Agent — RAG-Powered Investigation

Uses ChromaDB RAG to find similar past fraud cases.
Generates an explainable investigation report.
Only triggered for medium-high risk transactions.
"""

import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.orchestrator.state import AgentState
from app.schemas.agent_models import InvestigationAgentOutput
from app.rag.case_retriever import CaseRetriever
from app.config import settings
from app.observability.langsmith_tracer import trace_agent

logger = logging.getLogger(__name__)

INVESTIGATION_AGENT_PROMPT = """You are the Investigation Agent in a fraud detection system.

You have retrieved similar past fraud cases from the knowledge base.
Your job:
1. Analyse the current transaction against similar past cases
2. Identify matching fraud patterns
3. Assess evidence strength (WEAK | MODERATE | STRONG)
4. Write a clear investigation summary for human reviewers
5. List the most relevant similar case IDs

Be factual and precise. Human investigators will rely on this report.
Respond ONLY in valid JSON matching InvestigationAgentOutput schema.
"""


@trace_agent("investigation_agent")
async def investigation_agent_node(state: AgentState) -> dict:
    """Investigation agent — RAG retrieval + explainable case summary."""
    logger.info(f"[INVESTIGATION_AGENT] Investigating {state['transaction_id']}")

    tx = state["transaction_data"]
    fraud_out = state.get("fraud_output")

    # ── RAG retrieval ─────────────────────────────────────────────────────────
    retriever = CaseRetriever()
    query = f"{tx.get('merchant')} {tx.get('merchant_category')} {tx.get('country')} fraud"
    if fraud_out and fraud_out.anomaly_type:
        query += f" {fraud_out.anomaly_type}"

    similar_cases = await retriever.retrieve(query=query, k=5)
    logger.info(f"[INVESTIGATION_AGENT] Found {len(similar_cases)} similar cases")

    # ── LLM investigation report ──────────────────────────────────────────────
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(InvestigationAgentOutput)

    cases_text = "\n\n".join([
        f"Case {c['case_id']}: {c['summary']} (outcome: {c['outcome']})"
        for c in similar_cases
    ])

    messages = [
        SystemMessage(content=INVESTIGATION_AGENT_PROMPT),
        HumanMessage(content=f"""
Current Transaction:
- Transaction ID: {state['transaction_id']}
- Amount: {tx.get('amount')} {tx.get('currency')}
- Merchant: {tx.get('merchant')} ({tx.get('merchant_category')})
- Country: {tx.get('country')}
- Fraud score: {fraud_out.fraud_score if fraud_out else 'N/A'}
- Fraud indicators: {fraud_out.fraud_indicators if fraud_out else []}

Similar Past Cases (from knowledge base):
{cases_text if cases_text else 'No similar cases found.'}

Write the investigation report.
""")
    ]

    output: InvestigationAgentOutput = await llm.ainvoke(messages)
    logger.info(f"[INVESTIGATION_AGENT] Evidence: {output.evidence_strength} | Cases matched: {output.similar_cases_found}")

    return {
        "investigation_output": output,
        "agents_completed": ["investigation_agent"],
        "mcp_tools_called": [],
        "messages": [HumanMessage(content=f"Investigation Agent: evidence={output.evidence_strength}, cases={output.similar_cases_found}")]
    }

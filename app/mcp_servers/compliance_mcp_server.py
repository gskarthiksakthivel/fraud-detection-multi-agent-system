"""
compliance_mcp_server.py
========================
LAYER: MCP Server 2 — Compliance Tools

FastMCP server exposing 5 compliance tools:
  - kyc_status
  - sanctions_check
  - aml_screening
  - gdpr_audit_log
  - generate_sar_report

Runs as separate process on port 8003.
In production wraps real KYC/AML providers (Refinitiv, ComplyAdvantage).
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List
import random
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

mcp = FastMCP("Compliance MCP Server")

# ── High-risk country list (simplified) ──────────────────────────────────────
HIGH_RISK_COUNTRIES = {"RU", "NG", "KP", "IR", "BY", "CU", "SY", "MM"}
SANCTIONED_MERCHANTS = {"CryptoExchange XYZ", "ShadowBank Corp", "OffshoreVault Ltd"}


@mcp.tool()
async def kyc_status(account_id: str) -> dict:
    """
    Check KYC verification status for an account holder.
    Returns KYC tier, verification date, and any outstanding requirements.
    """
    logger.info(f"[COMPLIANCE_MCP] kyc_status: account={account_id}")

    # Deterministic for demo: accounts ending in 0 or 1 have issues
    last_char = account_id[-1] if account_id else "5"
    kyc_ok = last_char not in ("0", "1")

    return {
        "account_id": account_id,
        "kyc_status": "VERIFIED" if kyc_ok else "PENDING",
        "kyc_tier": "ENHANCED" if kyc_ok else "BASIC",
        "last_verified": "2024-11-01" if kyc_ok else None,
        "outstanding_requirements": [] if kyc_ok else ["proof_of_address", "source_of_funds"],
        "enhanced_due_diligence": not kyc_ok
    }


@mcp.tool()
async def sanctions_check(account_id: str, merchant: str, country: str) -> dict:
    """
    Screen against OFAC, EU, UN and national sanctions lists.
    """
    logger.info(f"[COMPLIANCE_MCP] sanctions_check: merchant={merchant} country={country}")

    sanctions_hit = merchant in SANCTIONED_MERCHANTS or country in {"KP", "IR", "SY"}
    lists_checked = ["OFAC_SDN", "EU_CONSOLIDATED", "UN_SECURITY_COUNCIL", "NL_DNB"]

    return {
        "account_id": account_id,
        "merchant": merchant,
        "country": country,
        "sanctions_hit": sanctions_hit,
        "matched_list": "OFAC_SDN" if sanctions_hit else None,
        "match_confidence": 0.97 if sanctions_hit else 0.0,
        "lists_checked": lists_checked,
        "check_timestamp": datetime.utcnow().isoformat(),
        "requires_immediate_block": sanctions_hit
    }


@mcp.tool()
async def aml_screening(account_id: str, amount: float, merchant_category: str) -> dict:
    """
    AML screening — detect money laundering typologies.
    Checks structuring, layering, high-risk category patterns.
    """
    logger.info(f"[COMPLIANCE_MCP] aml_screening: account={account_id} amount={amount} cat={merchant_category}")

    structuring = 9000 < amount < 10000  # Classic structuring below reporting threshold
    high_risk_cat = merchant_category in ("CRYPTO", "CASINO", "MONEY_TRANSFER")
    aml_flag = structuring or high_risk_cat or amount > 50000

    typologies = []
    if structuring:
        typologies.append("STRUCTURING_BELOW_THRESHOLD")
    if high_risk_cat:
        typologies.append("HIGH_RISK_MERCHANT_CATEGORY")
    if amount > 50000:
        typologies.append("LARGE_CASH_EQUIVALENT")

    return {
        "account_id": account_id,
        "aml_flagged": aml_flag,
        "typologies_detected": typologies,
        "risk_score": round(min(1.0, 0.3 * len(typologies) + (0.4 if structuring else 0)), 2),
        "enhanced_monitoring": aml_flag,
        "reporting_threshold_breach": amount >= 10000,
        "check_timestamp": datetime.utcnow().isoformat()
    }


@mcp.tool()
async def gdpr_audit_log(
    transaction_id: str,
    account_id: str,
    checks_performed: List[str],
    outcome: str
) -> dict:
    """
    Write a GDPR-compliant audit log entry.
    Records what personal data was accessed, by which system, for what purpose.
    """
    audit_id = str(uuid.uuid4())
    logger.info(f"[COMPLIANCE_MCP] gdpr_audit_log: tx={transaction_id} outcome={outcome}")

    return {
        "audit_id": audit_id,
        "transaction_id": transaction_id,
        "account_id": account_id,
        "data_accessed": ["transaction_data", "account_metadata"],
        "processing_purpose": "FRAUD_DETECTION_ART6_1F_GDPR",
        "legal_basis": "Article 6(1)(f) GDPR — legitimate interest",
        "checks_performed": checks_performed,
        "outcome": outcome,
        "retention_period_days": 2555,  # 7 years for financial records
        "logged_at": datetime.utcnow().isoformat(),
        "data_processor": "fraud-agentic-ai-v1.0"
    }


@mcp.tool()
async def generate_sar_report(
    transaction_id: str,
    account_id: str,
    suspicious_activity_description: str,
    aml_typologies: List[str]
) -> dict:
    """
    Generate a Suspicious Activity Report (SAR) for regulatory filing.
    In production this submits to FIU-NL (Dutch Financial Intelligence Unit).
    """
    sar_id = f"SAR-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
    logger.warning(f"[COMPLIANCE_MCP] generate_sar: tx={transaction_id} sar={sar_id}")

    return {
        "sar_id": sar_id,
        "transaction_id": transaction_id,
        "account_id": account_id,
        "status": "DRAFT",  # Requires human review before submission
        "description": suspicious_activity_description,
        "typologies": aml_typologies,
        "reporting_entity": "BANK_NL_001",
        "submission_deadline": "24h",
        "filing_authority": "FIU-NL",
        "created_at": datetime.utcnow().isoformat(),
        "requires_human_review": True
    }


if __name__ == "__main__":
    from app.mcp_servers.rest_app import run_rest
    run_rest(mcp, port=8003)

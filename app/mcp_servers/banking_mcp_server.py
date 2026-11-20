"""
banking_mcp_server.py
=====================
LAYER: MCP Server 1 — Banking Tools

A FastMCP server exposing 6 banking tools to agents:
  - get_transaction_history
  - check_velocity
  - flag_transaction
  - freeze_account
  - get_account_info
  - get_risk_signals

Agents call these via MCPClient. This server runs as a separate process
(see docker-compose.yml — port 8002).

In production this wraps real banking core APIs behind a stable MCP contract.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

mcp = FastMCP("Banking MCP Server")


# ── Tool Input Schemas ────────────────────────────────────────────────────────

class TransactionHistoryInput(BaseModel):
    account_id: str = Field(..., description="Account ID to look up")
    hours: int = Field(default=24, ge=1, le=168, description="Look-back window in hours")


class VelocityInput(BaseModel):
    account_id: str
    window_minutes: int = Field(default=60, ge=5, le=1440)


class FlagTransactionInput(BaseModel):
    transaction_id: str
    reason: str
    score: float = Field(ge=0.0, le=1.0)


class FreezeAccountInput(BaseModel):
    account_id: str
    reason: str
    initiated_by: str = Field(default="fraud_agent")


class AccountInfoInput(BaseModel):
    account_id: str


class RiskSignalsInput(BaseModel):
    account_id: str
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_transaction_history(account_id: str, hours: int = 24) -> dict:
    """
    Retrieve recent transaction history for an account.
    Returns list of transactions with amounts, merchants, timestamps.
    """
    logger.info(f"[BANKING_MCP] get_transaction_history: account={account_id} hours={hours}")

    # Mock data — replace with real core banking API call in production
    tx_count = random.randint(1, 15)
    transactions = []
    for i in range(tx_count):
        transactions.append({
            "id": f"TX-{random.randint(10000, 99999)}",
            "amount": round(random.uniform(10, 5000), 2),
            "merchant": random.choice(["Amazon", "Albert Heijn", "Shell", "CryptoExchange", "Jumbo"]),
            "category": random.choice(["RETAIL", "FOOD", "FUEL", "CRYPTO"]),
            "timestamp": datetime.utcnow().isoformat(),
            "country": random.choice(["NL", "BE", "DE", "FR"]),
            "status": "COMPLETED"
        })

    return {
        "account_id": account_id,
        "transaction_count": tx_count,
        "window_hours": hours,
        "transactions": transactions
    }


@mcp.tool()
async def check_velocity(account_id: str, window_minutes: int = 60) -> dict:
    """
    Check transaction velocity for an account in a time window.
    High velocity (>5 in 60 mins) is a fraud indicator.
    """
    logger.info(f"[BANKING_MCP] check_velocity: account={account_id} window={window_minutes}m")

    tx_count = random.randint(0, 10)
    velocity_flag = tx_count > 5

    return {
        "account_id": account_id,
        "window_minutes": window_minutes,
        "transaction_count": tx_count,
        "velocity_flag": velocity_flag,
        "threshold": 5,
        "status": "VELOCITY_ABUSE" if velocity_flag else "NORMAL"
    }


@mcp.tool()
async def flag_transaction(transaction_id: str, reason: str, score: float) -> dict:
    """
    Flag a transaction for review in the core banking system.
    Creates a fraud alert record.
    """
    logger.info(f"[BANKING_MCP] flag_transaction: tx={transaction_id} reason={reason} score={score:.2f}")

    return {
        "transaction_id": transaction_id,
        "flagged": True,
        "alert_id": f"ALERT-{random.randint(10000, 99999)}",
        "reason": reason,
        "score": score,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ALERT_CREATED"
    }


@mcp.tool()
async def freeze_account(account_id: str, reason: str, initiated_by: str = "fraud_agent") -> dict:
    """
    Freeze an account — emergency action for CRITICAL fraud detections.
    Requires audit trail entry.
    """
    logger.warning(f"[BANKING_MCP] freeze_account: account={account_id} reason={reason}")

    return {
        "account_id": account_id,
        "frozen": True,
        "freeze_id": f"FREEZE-{random.randint(10000, 99999)}",
        "reason": reason,
        "initiated_by": initiated_by,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ACCOUNT_FROZEN",
        "notification_sent": True
    }


@mcp.tool()
async def get_account_info(account_id: str) -> dict:
    """
    Retrieve account metadata: customer tier, account age, previous fraud history.
    """
    logger.info(f"[BANKING_MCP] get_account_info: account={account_id}")

    return {
        "account_id": account_id,
        "customer_tier": random.choice(["STANDARD", "PREMIUM", "PRIVATE"]),
        "account_age_days": random.randint(30, 3650),
        "previous_fraud_flags": random.randint(0, 3),
        "country_of_registration": "NL",
        "kyc_tier": random.choice(["BASIC", "ENHANCED", "FULL"]),
        "status": "ACTIVE"
    }


@mcp.tool()
async def get_risk_signals(account_id: str, ip_address: Optional[str] = None,
                           device_fingerprint: Optional[str] = None) -> dict:
    """
    Get device and IP risk signals for a transaction.
    Checks Tor exit nodes, known fraud devices, geo-IP mismatch.
    """
    logger.info(f"[BANKING_MCP] get_risk_signals: account={account_id} ip={ip_address}")

    tor_exit = ip_address and ip_address.startswith("185.220")
    geo_mismatch = random.choice([True, False])

    return {
        "account_id": account_id,
        "ip_address": ip_address,
        "is_tor_exit_node": tor_exit,
        "geo_mismatch": geo_mismatch,
        "device_known": random.choice([True, False]),
        "device_risk_score": round(random.uniform(0, 1), 2),
        "ip_reputation": "BAD" if tor_exit else random.choice(["GOOD", "NEUTRAL", "BAD"])
    }


if __name__ == "__main__":

    from app.mcp_servers.rest_app import run_rest
    run_rest(mcp, port=8002)

"""
test_banking_mcp_contract.py
============================
Contract tests — Banking MCP server must always return these schemas.
Breaks the build if Banking MCP changes output shape without updating agents.
Tests call the tool functions directly (no HTTP).
"""

import pytest
from app.mcp_servers.banking_mcp_server import (
    get_transaction_history, check_velocity,
    flag_transaction, freeze_account, get_account_info, get_risk_signals
)

REQUIRED_HISTORY_FIELDS = {"account_id", "transaction_count", "window_hours", "transactions"}
REQUIRED_VELOCITY_FIELDS = {"account_id", "velocity_flag", "transaction_count", "threshold", "status"}
REQUIRED_FLAG_FIELDS = {"flagged", "alert_id", "transaction_id", "status"}
REQUIRED_FREEZE_FIELDS = {"frozen", "freeze_id", "account_id", "notification_sent"}
REQUIRED_ACCOUNT_FIELDS = {"account_id", "customer_tier", "account_age_days", "previous_fraud_flags"}
REQUIRED_RISK_FIELDS = {"is_tor_exit_node", "geo_mismatch", "device_known", "ip_reputation"}


class TestBankingMCPContract:
    @pytest.mark.asyncio
    async def test_get_transaction_history_contract(self):
        result = await get_transaction_history(account_id="ACC-TEST")
        assert REQUIRED_HISTORY_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_HISTORY_FIELDS - result.keys()}"
        assert isinstance(result["transactions"], list)

    @pytest.mark.asyncio
    async def test_check_velocity_contract(self):
        result = await check_velocity(account_id="ACC-TEST")
        assert REQUIRED_VELOCITY_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_VELOCITY_FIELDS - result.keys()}"
        assert result["status"] in ("NORMAL", "VELOCITY_ABUSE"), \
            f"Invalid status: {result['status']}"

    @pytest.mark.asyncio
    async def test_flag_transaction_contract(self):
        result = await flag_transaction("TX-TEST", "test_reason", 0.5)
        assert REQUIRED_FLAG_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_FLAG_FIELDS - result.keys()}"
        assert isinstance(result["flagged"], bool)

    @pytest.mark.asyncio
    async def test_freeze_account_contract(self):
        result = await freeze_account("ACC-TEST", "test_reason")
        assert REQUIRED_FREEZE_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_FREEZE_FIELDS - result.keys()}"
        assert isinstance(result["frozen"], bool)

    @pytest.mark.asyncio
    async def test_get_account_info_contract(self):
        result = await get_account_info("ACC-TEST")
        assert REQUIRED_ACCOUNT_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_ACCOUNT_FIELDS - result.keys()}"

    @pytest.mark.asyncio
    async def test_get_risk_signals_contract(self):
        result = await get_risk_signals("ACC-TEST", ip_address="84.104.1.1")
        assert REQUIRED_RISK_FIELDS.issubset(result.keys()), \
            f"Missing fields: {REQUIRED_RISK_FIELDS - result.keys()}"
        assert result["ip_reputation"] in ("GOOD", "NEUTRAL", "BAD")

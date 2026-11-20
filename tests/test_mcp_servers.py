"""
test_mcp_servers.py
===================
Unit tests for both MCP server tools.
Tests tool functions directly (no HTTP layer needed).
"""

import pytest
from app.mcp_servers.banking_mcp_server import (
    get_transaction_history, check_velocity,
    flag_transaction, freeze_account, get_account_info, get_risk_signals
)
from app.mcp_servers.compliance_mcp_server import (
    kyc_status, sanctions_check, aml_screening, gdpr_audit_log, generate_sar_report
)


class TestBankingMCPServer:
    @pytest.mark.asyncio
    async def test_get_transaction_history_returns_list(self):
        result = await get_transaction_history(account_id="ACC-001", hours=24)
        assert "transactions" in result
        assert isinstance(result["transactions"], list)
        assert result["account_id"] == "ACC-001"

    @pytest.mark.asyncio
    async def test_check_velocity_returns_flag(self):
        result = await check_velocity(account_id="ACC-001", window_minutes=60)
        assert "velocity_flag" in result
        assert isinstance(result["velocity_flag"], bool)
        assert result["threshold"] == 5

    @pytest.mark.asyncio
    async def test_flag_transaction_creates_alert(self):
        result = await flag_transaction(
            transaction_id="TX-001",
            reason="velocity_abuse",
            score=0.87
        )
        assert result["flagged"] is True
        assert "alert_id" in result
        assert result["transaction_id"] == "TX-001"

    @pytest.mark.asyncio
    async def test_freeze_account_returns_frozen(self):
        result = await freeze_account(
            account_id="ACC-001",
            reason="critical_fraud",
            initiated_by="fraud_agent"
        )
        assert result["frozen"] is True
        assert "freeze_id" in result
        assert result["notification_sent"] is True

    @pytest.mark.asyncio
    async def test_get_risk_signals_tor_detection(self):
        # Tor exit node IP starts with 185.220
        result = await get_risk_signals(
            account_id="ACC-001",
            ip_address="185.220.101.1"
        )
        assert result["is_tor_exit_node"] is True
        assert result["ip_reputation"] == "BAD"

    @pytest.mark.asyncio
    async def test_get_risk_signals_clean_ip(self):
        result = await get_risk_signals(
            account_id="ACC-001",
            ip_address="84.104.1.1"
        )
        assert result["is_tor_exit_node"] is False


class TestComplianceMCPServer:
    @pytest.mark.asyncio
    async def test_kyc_status_verified_account(self):
        result = await kyc_status(account_id="ACC-005")
        assert "kyc_status" in result
        assert result["kyc_status"] in ("VERIFIED", "PENDING", "FAILED", "EXPIRED")

    @pytest.mark.asyncio
    async def test_kyc_status_pending_account(self):
        # Accounts ending in 0 or 1 have pending KYC
        result = await kyc_status(account_id="ACC-000")
        assert result["kyc_status"] == "PENDING"
        assert len(result["outstanding_requirements"]) > 0

    @pytest.mark.asyncio
    async def test_sanctions_check_hit_on_sanctioned_merchant(self):
        result = await sanctions_check(
            account_id="ACC-001",
            merchant="CryptoExchange XYZ",
            country="NL"
        )
        assert result["sanctions_hit"] is True
        assert result["requires_immediate_block"] is True

    @pytest.mark.asyncio
    async def test_sanctions_check_clean_merchant(self):
        result = await sanctions_check(
            account_id="ACC-001",
            merchant="Albert Heijn",
            country="NL"
        )
        assert result["sanctions_hit"] is False

    @pytest.mark.asyncio
    async def test_aml_structuring_detection(self):
        # EUR 9,800 is classic structuring below EUR 10,000 threshold
        result = await aml_screening(
            account_id="ACC-001",
            amount=9800.0,
            merchant_category="RETAIL"
        )
        assert result["aml_flagged"] is True
        assert "STRUCTURING_BELOW_THRESHOLD" in result["typologies_detected"]

    @pytest.mark.asyncio
    async def test_aml_crypto_flag(self):
        result = await aml_screening(
            account_id="ACC-001",
            amount=500.0,
            merchant_category="CRYPTO"
        )
        assert result["aml_flagged"] is True
        assert "HIGH_RISK_MERCHANT_CATEGORY" in result["typologies_detected"]

    @pytest.mark.asyncio
    async def test_gdpr_audit_log_creates_record(self):
        result = await gdpr_audit_log(
            transaction_id="TX-001",
            account_id="ACC-001",
            checks_performed=["kyc", "sanctions", "aml"],
            outcome="CLEAN"
        )
        assert "audit_id" in result
        assert result["retention_period_days"] == 2555
        assert "GDPR" in result["processing_purpose"]

    @pytest.mark.asyncio
    async def test_generate_sar_report(self):
        result = await generate_sar_report(
            transaction_id="TX-001",
            account_id="ACC-001",
            suspicious_activity_description="Structuring detected",
            aml_typologies=["STRUCTURING_BELOW_THRESHOLD"]
        )
        assert result["sar_id"].startswith("SAR-")
        assert result["requires_human_review"] is True
        assert result["filing_authority"] == "FIU-NL"

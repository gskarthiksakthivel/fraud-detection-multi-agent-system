"""
test_compliance_mcp_contract.py
================================
Contract tests — Compliance MCP must always return these schemas.
"""

import pytest
from app.mcp_servers.compliance_mcp_server import (
    kyc_status, sanctions_check, aml_screening, gdpr_audit_log, generate_sar_report
)

REQUIRED_KYC_FIELDS = {"account_id", "kyc_status", "kyc_tier", "outstanding_requirements"}
REQUIRED_SANCTIONS_FIELDS = {"sanctions_hit", "lists_checked", "requires_immediate_block"}
REQUIRED_AML_FIELDS = {"aml_flagged", "typologies_detected", "risk_score", "reporting_threshold_breach"}
REQUIRED_GDPR_FIELDS = {"audit_id", "legal_basis", "retention_period_days", "logged_at"}
REQUIRED_SAR_FIELDS = {"sar_id", "status", "requires_human_review", "filing_authority"}

VALID_KYC_STATUSES = {"VERIFIED", "PENDING", "FAILED", "EXPIRED"}


class TestComplianceMCPContract:
    @pytest.mark.asyncio
    async def test_kyc_status_contract(self):
        result = await kyc_status(account_id="ACC-TEST")
        assert REQUIRED_KYC_FIELDS.issubset(result.keys())
        assert result["kyc_status"] in VALID_KYC_STATUSES

    @pytest.mark.asyncio
    async def test_sanctions_check_contract(self):
        result = await sanctions_check("ACC-TEST", "TestMerchant", "NL")
        assert REQUIRED_SANCTIONS_FIELDS.issubset(result.keys())
        assert isinstance(result["sanctions_hit"], bool)
        assert isinstance(result["lists_checked"], list)

    @pytest.mark.asyncio
    async def test_aml_screening_contract(self):
        result = await aml_screening("ACC-TEST", 1000.0, "RETAIL")
        assert REQUIRED_AML_FIELDS.issubset(result.keys())
        assert isinstance(result["typologies_detected"], list)
        assert 0.0 <= result["risk_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_gdpr_audit_log_contract(self):
        result = await gdpr_audit_log("TX-TEST", "ACC-TEST", ["kyc"], "CLEAN")
        assert REQUIRED_GDPR_FIELDS.issubset(result.keys())
        assert result["retention_period_days"] == 2555

    @pytest.mark.asyncio
    async def test_generate_sar_contract(self):
        result = await generate_sar_report("TX-TEST", "ACC-TEST", "Suspicious activity", ["STRUCTURING"])
        assert REQUIRED_SAR_FIELDS.issubset(result.keys())
        assert result["sar_id"].startswith("SAR-")
        assert result["filing_authority"] == "FIU-NL"

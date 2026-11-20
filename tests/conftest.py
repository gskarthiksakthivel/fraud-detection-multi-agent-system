"""
conftest.py
===========
Shared pytest fixtures — mock Redis, mock OpenAI, mock ChromaDB, sample transactions.
All tests import from here. No real services needed to run the test suite.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.models import TransactionRequest, RiskLevel
from app.schemas.agent_models import (
    FraudAgentOutput, ComplianceAgentOutput,
    RiskAgentOutput, InvestigationAgentOutput, EscalationAgentOutput
)
from app.orchestrator.state import AgentState
import time


@pytest.fixture
def sample_transaction():
    return {
        "transaction_id": "TX-TEST-001",
        "account_id": "ACC-001",
        "amount": 4999.99,
        "currency": "EUR",
        "merchant": "CryptoExchange XYZ",
        "merchant_category": "CRYPTO",
        "country": "RU",
        "ip_address": "185.220.101.1",
        "device_fingerprint": "test-device",
        "session_id": "SESSION-TEST-001"
    }


@pytest.fixture
def low_risk_transaction():
    return {
        "transaction_id": "TX-TEST-LOW-001",
        "account_id": "ACC-002",
        "amount": 45.50,
        "currency": "EUR",
        "merchant": "Albert Heijn",
        "merchant_category": "GROCERY",
        "country": "NL",
        "ip_address": "84.104.1.1",
        "session_id": "SESSION-LOW-001"
    }


@pytest.fixture
def sample_agent_state(sample_transaction):
    return AgentState(
        transaction_id="TX-TEST-001",
        session_id="SESSION-TEST-001",
        transaction_data=sample_transaction,
        messages=[],
        fraud_output=None,
        compliance_output=None,
        risk_output=None,
        investigation_output=None,
        escalation_output=None,
        next_agent="fraud_agent",
        agents_completed=[],
        should_escalate=False,
        mcp_tools_called=[],
        final_risk_level=None,
        final_fraud_score=0.0,
        escalation_status=None,
        final_summary=None,
        audit_trail_id=None,
        error=None,
        processing_start_ms=time.time() * 1000,
    )


@pytest.fixture
def mock_fraud_output():
    return FraudAgentOutput(
        is_fraud=True,
        fraud_score=0.87,
        fraud_indicators=["velocity_abuse", "geo_anomaly", "tor_exit_node"],
        anomaly_type="velocity_abuse",
        recommended_action="BLOCK",
        confidence=0.92,
        reasoning="Multiple fraud signals: high-risk country, Tor exit node, velocity abuse"
    )


@pytest.fixture
def mock_compliance_output():
    return ComplianceAgentOutput(
        kyc_passed=False,
        sanctions_hit=True,
        aml_flag=True,
        gdpr_issues=[],
        pci_dss_issues=[],
        compliance_notes="Sanctions hit on merchant. AML structuring pattern detected.",
        requires_sar=True,
        confidence=0.95
    )


@pytest.fixture
def mock_risk_output():
    return RiskAgentOutput(
        risk_level=RiskLevel.CRITICAL,
        risk_score=92.0,
        risk_factors=["fraud_score_high", "sanctions_hit", "aml_flag", "kyc_failed"],
        velocity_check="FAIL",
        geo_risk="HIGH",
        device_risk="HIGH",
        final_recommendation="BLOCK",
        confidence=0.93
    )


@pytest.fixture
def mock_redis():
    with patch("app.memory.redis_state.redis.from_url") as mock:
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.setex.return_value = True
        redis_mock.get.return_value = None
        redis_mock.delete.return_value = 1
        redis_mock.exists.return_value = False
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_openai_llm():
    with patch("langchain_openai.ChatOpenAI") as mock:
        llm_mock = AsyncMock()
        mock.return_value = llm_mock
        yield llm_mock


@pytest.fixture
def mock_mcp_client():
    with patch("app.mcp_servers.mcp_client.MCPClient") as mock:
        client_mock = AsyncMock()
        client_mock.call_tool.return_value = {"result": "mock_result", "status": "OK"}
        client_mock.health_check.return_value = True
        mock.return_value = client_mock
        yield client_mock

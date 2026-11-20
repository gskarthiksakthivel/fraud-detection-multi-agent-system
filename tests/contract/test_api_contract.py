"""
test_api_contract.py
====================
Contract tests — FastAPI response shapes must match OpenAPI spec.
Uses TestClient (no real services needed).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def get_auth_headers():
    from app.security.auth import create_access_token
    token = create_access_token("test-user")
    return {"Authorization": f"Bearer {token}"}


class TestHealthContract:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "services" in data

    def test_health_status_is_string(self):
        response = client.get("/health")
        assert isinstance(response.json()["status"], str)


class TestAnalyseContract:
    def test_analyse_requires_auth(self):
        payload = {"account_id": "ACC-001", "amount": 100.0, "merchant": "Test"}
        response = client.post("/api/v1/analyse", json=payload)
        assert response.status_code == 403

    def test_analyse_rejects_missing_account_id(self):
        headers = get_auth_headers()
        payload = {"amount": 100.0, "merchant": "Test"}  # Missing account_id
        response = client.post("/api/v1/analyse", json=payload, headers=headers)
        assert response.status_code == 422

    def test_analyse_rejects_negative_amount(self):
        headers = get_auth_headers()
        payload = {"account_id": "ACC-001", "amount": -100.0, "merchant": "Test"}
        response = client.post("/api/v1/analyse", json=payload, headers=headers)
        assert response.status_code == 422

    def test_analyse_rejects_zero_amount(self):
        headers = get_auth_headers()
        payload = {"account_id": "ACC-001", "amount": 0.0, "merchant": "Test"}
        response = client.post("/api/v1/analyse", json=payload, headers=headers)
        assert response.status_code == 422


class TestEscalationContract:
    def test_escalation_requires_auth(self):
        payload = {"transaction_id": "TX-001", "reason": "test",
                   "agent_name": "fraud_agent", "risk_level": "HIGH"}
        response = client.post("/api/v1/escalate", json=payload)
        assert response.status_code == 403

    def test_escalation_with_valid_token(self):
        headers = get_auth_headers()
        payload = {"transaction_id": "TX-001", "reason": "Test escalation",
                   "agent_name": "fraud_agent", "risk_level": "HIGH"}
        response = client.post("/api/v1/escalate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "escalation_id" in data
        assert "transaction_id" in data
        assert "status" in data

    def test_escalation_invalid_risk_level(self):
        headers = get_auth_headers()
        payload = {"transaction_id": "TX-001", "reason": "test",
                   "agent_name": "fraud_agent", "risk_level": "UNKNOWN_LEVEL"}
        response = client.post("/api/v1/escalate", json=payload, headers=headers)
        assert response.status_code == 422


class TestSessionContract:
    def test_session_not_found_returns_404(self):
        headers = get_auth_headers()
        with patch("app.main.state_manager.load_state", AsyncMock(return_value=None)):
            response = client.get("/api/v1/session/nonexistent-session", headers=headers)
            assert response.status_code == 404

    def test_openapi_schema_accessible(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/analyse" in schema["paths"]
        assert "/health" in schema["paths"]

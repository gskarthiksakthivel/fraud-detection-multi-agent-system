"""
test_orchestrator.py
====================
Integration tests for the LangGraph StateGraph.
Tests graph routing logic and conditional edges directly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.orchestrator.graph import should_escalate_immediately, route_after_risk
from app.schemas.agent_models import FraudAgentOutput, RiskAgentOutput
from app.schemas.models import RiskLevel
import time


def make_state(fraud_score=0.5, risk_score=50.0, risk_level=RiskLevel.MEDIUM):
    fraud_output = FraudAgentOutput(
        is_fraud=fraud_score >= 0.5,
        fraud_score=fraud_score,
        fraud_indicators=["test"],
        recommended_action="REVIEW",
        confidence=0.9,
        reasoning="Test"
    ) if fraud_score > 0 else None

    risk_output = RiskAgentOutput(
        risk_level=risk_level,
        risk_score=risk_score,
        risk_factors=["test"],
        velocity_check="PASS",
        geo_risk="LOW",
        device_risk="LOW",
        final_recommendation="REVIEW",
        confidence=0.9
    ) if risk_score > 0 else None

    return {
        "transaction_id": "TX-TEST",
        "session_id": "SESSION-TEST",
        "transaction_data": {},
        "messages": [],
        "fraud_output": fraud_output,
        "risk_output": risk_output,
        "agents_completed": [],
        "mcp_tools_called": [],
        "processing_start_ms": time.time() * 1000,
    }


class TestConditionalRouting:
    def test_critical_fraud_skips_to_escalation(self):
        state = make_state(fraud_score=0.95)
        result = should_escalate_immediately(state)
        assert result == "escalation_agent"

    def test_medium_fraud_goes_to_compliance(self):
        state = make_state(fraud_score=0.6)
        result = should_escalate_immediately(state)
        assert result == "compliance_agent"

    def test_low_fraud_goes_to_compliance(self):
        state = make_state(fraud_score=0.2)
        result = should_escalate_immediately(state)
        assert result == "compliance_agent"

    def test_high_risk_score_triggers_investigation(self):
        state = make_state(risk_score=75.0, risk_level=RiskLevel.HIGH)
        result = route_after_risk(state)
        assert result == "investigation_agent"

    def test_low_risk_score_skips_investigation(self):
        state = make_state(risk_score=20.0, risk_level=RiskLevel.LOW)
        result = route_after_risk(state)
        assert result == "escalation_agent"

    def test_medium_fraud_with_high_risk_triggers_investigation(self):
        state = make_state(fraud_score=0.65, risk_score=40.0)
        result = route_after_risk(state)
        assert result == "investigation_agent"


class TestGraphStructure:
    def test_graph_compiles_successfully(self):
        from app.orchestrator.graph import agent_graph
        assert agent_graph is not None

    def test_graph_has_all_nodes(self):
        from app.orchestrator.graph import agent_graph
        graph_nodes = list(agent_graph.get_graph().nodes.keys())
        expected = ["supervisor", "fraud_agent", "compliance_agent",
                    "risk_agent", "investigation_agent", "escalation_agent"]
        for node in expected:
            assert node in graph_nodes, f"Missing node: {node}"

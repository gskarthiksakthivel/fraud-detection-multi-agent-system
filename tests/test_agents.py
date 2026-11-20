"""
test_agents.py
==============
Unit tests for all 5 specialist agents.
All external calls (OpenAI, Redis, MCP) are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.agent_models import FraudAgentOutput, ComplianceAgentOutput, RiskAgentOutput
from app.schemas.models import RiskLevel


class TestFraudAgent:
    @pytest.mark.asyncio
    async def test_fraud_agent_returns_output(self, sample_agent_state, mock_fraud_output, mock_mcp_client):
        with patch("app.agents.fraud_agent.MCPClient", return_value=mock_mcp_client):
            with patch("app.agents.fraud_agent.ChatOpenAI") as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_fraud_output)
                mock_llm_class.return_value = mock_llm

                from app.agents.fraud_agent import fraud_agent_node
                result = await fraud_agent_node(sample_agent_state)

                assert "fraud_output" in result
                assert result["final_fraud_score"] == mock_fraud_output.fraud_score
                assert "fraud_agent" in result["agents_completed"]

    @pytest.mark.asyncio
    async def test_fraud_agent_calls_mcp_tools(self, sample_agent_state, mock_fraud_output):
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {"transactions": [], "velocity_flag": False}
        with patch("app.agents.fraud_agent.MCPClient", return_value=mock_mcp):
            with patch("app.agents.fraud_agent.ChatOpenAI") as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_fraud_output)
                mock_llm_class.return_value = mock_llm

                from app.agents.fraud_agent import fraud_agent_node
                result = await fraud_agent_node(sample_agent_state)

                assert mock_mcp.call_tool.called
                calls = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
                assert "get_transaction_history" in calls
                assert "check_velocity" in calls

    @pytest.mark.asyncio
    async def test_fraud_agent_flags_high_score_transaction(self, sample_agent_state, mock_fraud_output):
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {"status": "OK"}
        with patch("app.agents.fraud_agent.MCPClient", return_value=mock_mcp):
            with patch("app.agents.fraud_agent.ChatOpenAI") as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_fraud_output)
                mock_llm_class.return_value = mock_llm

                from app.agents.fraud_agent import fraud_agent_node
                result = await fraud_agent_node(sample_agent_state)

                # fraud_score = 0.87 >= 0.7 → flag_transaction should be called
                tool_calls = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
                assert "flag_transaction" in tool_calls


class TestComplianceAgent:
    @pytest.mark.asyncio
    async def test_compliance_agent_returns_output(self, sample_agent_state, mock_compliance_output):
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {"kyc_status": "VERIFIED", "sanctions_hit": False, "aml_flagged": False}
        with patch("app.agents.compliance_agent.MCPClient", return_value=mock_mcp):
            with patch("app.agents.compliance_agent.ChatOpenAI") as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_compliance_output)
                mock_llm_class.return_value = mock_llm

                from app.agents.compliance_agent import compliance_agent_node
                result = await compliance_agent_node(sample_agent_state)

                assert "compliance_output" in result
                assert "compliance_agent" in result["agents_completed"]

    @pytest.mark.asyncio
    async def test_compliance_agent_calls_three_mcp_tools(self, sample_agent_state, mock_compliance_output):
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {}
        with patch("app.agents.compliance_agent.MCPClient", return_value=mock_mcp):
            with patch("app.agents.compliance_agent.ChatOpenAI") as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_compliance_output)
                mock_llm_class.return_value = mock_llm

                from app.agents.compliance_agent import compliance_agent_node
                await compliance_agent_node(sample_agent_state)

                tool_calls = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
                assert "kyc_status" in tool_calls
                assert "sanctions_check" in tool_calls
                assert "aml_screening" in tool_calls


class TestRiskAgent:
    @pytest.mark.asyncio
    async def test_risk_agent_returns_critical_for_high_inputs(self, sample_agent_state, mock_fraud_output, mock_compliance_output, mock_risk_output):
        state = dict(sample_agent_state)
        state["fraud_output"] = mock_fraud_output
        state["compliance_output"] = mock_compliance_output

        with patch("app.agents.risk_agent.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_risk_output)
            mock_llm_class.return_value = mock_llm

            from app.agents.risk_agent import risk_agent_node
            result = await risk_agent_node(state)

            assert result["final_risk_level"] == RiskLevel.CRITICAL
            assert "risk_agent" in result["agents_completed"]

    @pytest.mark.asyncio
    async def test_risk_agent_handles_missing_prior_outputs(self, sample_agent_state, mock_risk_output):
        with patch("app.agents.risk_agent.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_risk_output.risk_level = RiskLevel.LOW
            mock_llm.with_structured_output.return_value = AsyncMock(return_value=mock_risk_output)
            mock_llm_class.return_value = mock_llm

            from app.agents.risk_agent import risk_agent_node
            result = await risk_agent_node(sample_agent_state)

            assert "risk_output" in result


class TestEscalationAgent:
    @pytest.mark.asyncio
    async def test_escalation_agent_auto_blocks_critical(self, sample_agent_state, mock_fraud_output, mock_compliance_output, mock_risk_output):
        from app.schemas.agent_models import EscalationAgentOutput
        escalation_output = EscalationAgentOutput(
            should_escalate=True,
            escalation_priority="P1",
            escalation_reason="Critical fraud + sanctions hit",
            auto_block=True,
            notify_channels=["slack", "pagerduty"],
            audit_message="Auto-blocked: CRITICAL risk, sanctions hit",
            confidence=0.97
        )

        state = dict(sample_agent_state)
        state["fraud_output"] = mock_fraud_output
        state["compliance_output"] = mock_compliance_output
        state["risk_output"] = mock_risk_output

        with patch("app.agents.escalation_agent.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value = AsyncMock(return_value=escalation_output)
            mock_llm_class.return_value = mock_llm
            with patch("app.agents.escalation_agent.write_audit_trail", AsyncMock()):
                from app.agents.escalation_agent import escalation_agent_node
                result = await escalation_agent_node(state)

                from app.schemas.models import EscalationStatus
                assert result["escalation_status"] == EscalationStatus.AUTO_BLOCKED
                assert result["audit_trail_id"] is not None

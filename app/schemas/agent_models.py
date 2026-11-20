"""
agent_models.py
===============
LAYER: Agent Structured Outputs

Pydantic models for LLM structured output enforcement per agent.
Each agent's LLM call is forced to return one of these shapes via
OpenAI JSON mode + Pydantic validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.models import RiskLevel


class FraudAgentOutput(BaseModel):
    """Structured output enforced on the Fraud Detection Agent LLM call."""
    is_fraud: bool
    fraud_score: float = Field(ge=0.0, le=1.0, description="0=clean 1=definite fraud")
    fraud_indicators: List[str] = Field(description="List of detected fraud signals")
    anomaly_type: Optional[str] = Field(default=None, description="e.g. velocity_abuse, geo_anomaly")
    recommended_action: str = Field(description="BLOCK | REVIEW | ALLOW")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ComplianceAgentOutput(BaseModel):
    """Structured output for the Compliance Agent."""
    kyc_passed: bool
    sanctions_hit: bool
    aml_flag: bool
    gdpr_issues: List[str] = []
    pci_dss_issues: List[str] = []
    compliance_notes: str
    requires_sar: bool = Field(description="Suspicious Activity Report required?")
    confidence: float = Field(ge=0.0, le=1.0)


class RiskAgentOutput(BaseModel):
    """Structured output for the Risk Scoring Agent."""
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_factors: List[str]
    velocity_check: str = Field(description="PASS | WARN | FAIL")
    geo_risk: str = Field(description="LOW | MEDIUM | HIGH")
    device_risk: str = Field(description="LOW | MEDIUM | HIGH")
    final_recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvestigationAgentOutput(BaseModel):
    """Structured output for the RAG-powered Investigation Agent."""
    case_summary: str
    similar_cases_found: int
    similar_case_ids: List[str] = []
    pattern_match: Optional[str] = None
    investigation_notes: str
    evidence_strength: str = Field(description="WEAK | MODERATE | STRONG")
    confidence: float = Field(ge=0.0, le=1.0)


class EscalationAgentOutput(BaseModel):
    """Structured output for the Escalation Agent."""
    should_escalate: bool
    escalation_priority: str = Field(description="P1 | P2 | P3")
    escalation_reason: str
    auto_block: bool
    notify_channels: List[str] = Field(description="e.g. ['slack', 'email', 'pagerduty']")
    audit_message: str
    confidence: float = Field(ge=0.0, le=1.0)


class SupervisorRouting(BaseModel):
    """Structured output for supervisor routing decisions."""
    next_agent: str = Field(description="Which agent to call next")
    reason: str
    priority: int = Field(ge=1, le=5, description="1=highest")
    skip_agents: List[str] = Field(default=[], description="Agents to skip this run")

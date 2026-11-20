"""
output_validator.py
===================
LAYER: Guardrails — Output Validation

Validates LLM structured outputs:
1. Schema validation (via Pydantic — already done by .with_structured_output())
2. Hallucination checks — detects suspicious patterns in agent reasoning
3. Confidence threshold enforcement
4. Consistency checks across agent outputs

Called after each agent produces its structured output.
"""

import logging
import re
from typing import Optional
from app.schemas.agent_models import (
    FraudAgentOutput, ComplianceAgentOutput,
    RiskAgentOutput, InvestigationAgentOutput, EscalationAgentOutput
)

logger = logging.getLogger(__name__)

MIN_CONFIDENCE_THRESHOLD = 0.3
HALLUCINATION_PATTERNS = [
    r"as an ai",
    r"i cannot",
    r"i don't have access",
    r"my training data",
    r"i apologize",
    r"lorem ipsum",
]


def check_hallucination(text: str) -> bool:
    """Check if text contains hallucination markers."""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning(f"[VALIDATOR] Hallucination marker detected: '{pattern}'")
            return True
    return False


def validate_fraud_output(output: FraudAgentOutput) -> tuple[bool, Optional[str]]:
    """Validate fraud agent output for consistency and hallucinations."""
    if output.confidence < MIN_CONFIDENCE_THRESHOLD:
        return False, f"Confidence {output.confidence} below threshold {MIN_CONFIDENCE_THRESHOLD}"

    if output.fraud_score >= 0.8 and not output.fraud_indicators:
        return False, "High fraud score but no fraud indicators — suspicious output"

    if output.is_fraud and output.recommended_action == "ALLOW":
        return False, "Contradiction: is_fraud=True but action=ALLOW"

    if check_hallucination(output.reasoning):
        return False, "Hallucination detected in reasoning"

    return True, None


def validate_risk_output(output: RiskAgentOutput) -> tuple[bool, Optional[str]]:
    """Validate risk agent output."""
    if output.risk_score < 0 or output.risk_score > 100:
        return False, f"Risk score {output.risk_score} out of range [0, 100]"

    if output.risk_level == "CRITICAL" and output.risk_score < 80:
        return False, f"CRITICAL risk level but score only {output.risk_score}"

    if output.confidence < MIN_CONFIDENCE_THRESHOLD:
        return False, f"Confidence {output.confidence} too low"

    return True, None


def validate_escalation_output(output: EscalationAgentOutput) -> tuple[bool, Optional[str]]:
    """Validate escalation agent output."""
    valid_priorities = {"P1", "P2", "P3"}
    if output.escalation_priority not in valid_priorities:
        return False, f"Invalid priority: {output.escalation_priority}"

    if output.auto_block and output.escalation_priority == "P3":
        return False, "Contradiction: auto_block=True but priority=P3 (should be P1/P2)"

    if check_hallucination(output.audit_message):
        return False, "Hallucination in audit message"

    return True, None

"""
eval_metrics.py
===============
LAYER: Evaluation — Custom Scoring Metrics

Scoring functions for each evaluation dimension:
- Risk level accuracy
- Fraud score threshold correctness
- Agent routing coverage
- PII leakage detection
- Hallucination rate
- Tool call correctness
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

RISK_LEVEL_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# Re-use PII patterns for output checking
PII_CHECK_PATTERNS = [
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b",           # IBAN
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b",                # Card number
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",  # Email
]


@dataclass
class EvalResult:
    case_id: str
    description: str
    passed: bool
    overall_score: float
    dimension_scores: Dict[str, float]
    latency_ms: float
    errors: List[str] = field(default_factory=list)
    final_state_summary: Dict = field(default_factory=dict)


def score_risk_level(actual: str, expected: str) -> float:
    """
    Score risk level — exact match = 1.0, one level off = 0.5, two+ off = 0.0.
    """
    actual = actual.upper().strip()
    expected = expected.upper().strip()
    if actual == expected:
        return 1.0
    actual_idx = RISK_LEVEL_ORDER.get(actual, -1)
    expected_idx = RISK_LEVEL_ORDER.get(expected, -1)
    if actual_idx == -1 or expected_idx == -1:
        return 0.0
    diff = abs(actual_idx - expected_idx)
    if diff == 1:
        return 0.5
    return 0.0


def score_fraud_threshold(actual_score: float, min_score: float = None, max_score: float = None) -> float:
    """Score whether fraud score is within expected range."""
    if min_score is not None and actual_score < min_score:
        return 0.0
    if max_score is not None and actual_score > max_score:
        return 0.0
    return 1.0


def score_agent_coverage(actual_agents: List[str], required_agents: List[str]) -> float:
    """Score what fraction of required agents actually ran."""
    if not required_agents:
        return 1.0
    ran = sum(1 for a in required_agents if a in actual_agents)
    return ran / len(required_agents)


def check_pii_leakage(text: str) -> bool:
    """Return True if PII is detected in output text (a failure)."""
    if not text:
        return False
    for pattern in PII_CHECK_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def score_hallucination_rate(outputs: List[str]) -> float:
    """
    Score a batch of LLM outputs for hallucination markers.
    Returns fraction of clean outputs (higher = better).
    """
    if not outputs:
        return 1.0
    hallucination_patterns = [
        r"as an ai",
        r"i cannot",
        r"my training data",
        r"i don.t have access",
    ]
    clean = 0
    for output in outputs:
        output_lower = output.lower()
        if not any(re.search(p, output_lower) for p in hallucination_patterns):
            clean += 1
    return clean / len(outputs)


def score_tool_call_correctness(actual_tools: List[str], expected_tools: List[str]) -> float:
    """Score whether the correct MCP tools were called."""
    if not expected_tools:
        return 1.0
    correct = sum(1 for t in expected_tools if t in actual_tools)
    return correct / len(expected_tools)


def compute_aggregate_metrics(results: List[EvalResult]) -> dict:
    """Compute aggregate metrics across all eval results."""
    if not results:
        return {}

    total = len(results)
    passed = sum(1 for r in results if r.passed)

    return {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 3),
        "avg_score": round(sum(r.overall_score for r in results) / total, 3),
        "avg_latency_ms": round(sum(r.latency_ms for r in results) / total, 1),
        "p95_latency_ms": round(sorted(r.latency_ms for r in results)[int(0.95 * total)], 1),
        "error_rate": round(sum(1 for r in results if r.errors) / total, 3),
        "dimension_averages": {
            dim: round(sum(r.dimension_scores.get(dim, 0) for r in results) / total, 3)
            for dim in set(k for r in results for k in r.dimension_scores)
        }
    }

"""
run_evals.py
============
LAYER: Evaluation Pipeline

Runs the full eval dataset through the agent graph.
Scores accuracy, escalation correctness, agent routing, PII leakage.
Reports results to LangSmith evaluation datasets.

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --dataset evals/eval_dataset.json --output evals/results.json
"""

import asyncio
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from evals.eval_metrics import (
    score_risk_level, score_fraud_threshold, score_agent_coverage,
    check_pii_leakage, EvalResult
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def run_single_eval(case: dict) -> EvalResult:
    """Run one eval case through the agent graph and score it."""
    from app.orchestrator.graph import agent_graph
    from app.orchestrator.state import AgentState

    start_ms = time.time() * 1000
    session_id = f"EVAL-{case['id']}-{datetime.utcnow().strftime('%H%M%S')}"

    initial_state: AgentState = {
        "transaction_id": case["id"],
        "session_id": session_id,
        "transaction_data": case["input"],
        "messages": [],
        "fraud_output": None, "compliance_output": None,
        "risk_output": None, "investigation_output": None, "escalation_output": None,
        "next_agent": "fraud_agent", "agents_completed": [],
        "should_escalate": False, "mcp_tools_called": [],
        "final_risk_level": None, "final_fraud_score": 0.0,
        "escalation_status": None, "final_summary": None,
        "audit_trail_id": None, "error": None,
        "processing_start_ms": start_ms,
    }

    scores = {}
    errors = []

    try:
        final_state = await agent_graph.ainvoke(initial_state)
        latency_ms = time.time() * 1000 - start_ms

        expected = case.get("expected", {})

        # Score: risk level exact match
        if "risk_level" in expected:
            actual_risk = str(final_state.get("final_risk_level", "")).replace("RiskLevel.", "")
            scores["risk_level"] = score_risk_level(actual_risk, expected["risk_level"])

        # Score: fraud score within expected range
        if "fraud_score_min" in expected:
            actual_score = final_state.get("final_fraud_score", 0.0)
            scores["fraud_score_min"] = 1.0 if actual_score >= expected["fraud_score_min"] else 0.0

        if "fraud_score_max" in expected:
            actual_score = final_state.get("final_fraud_score", 0.0)
            scores["fraud_score_max"] = 1.0 if actual_score <= expected["fraud_score_max"] else 0.0

        # Score: escalation status
        if "escalation_status" in expected:
            actual_status = str(final_state.get("escalation_status", "")).replace("EscalationStatus.", "")
            scores["escalation_status"] = 1.0 if actual_status == expected["escalation_status"] else 0.0

        # Score: required agents ran
        if "agents_must_include" in expected:
            actual_agents = final_state.get("agents_completed", [])
            scores["agent_coverage"] = score_agent_coverage(actual_agents, expected["agents_must_include"])

        # Score: no PII in final output
        if expected.get("no_pii_in_output"):
            summary = final_state.get("final_summary", "")
            scores["no_pii"] = 0.0 if check_pii_leakage(summary) else 1.0

        overall_score = sum(scores.values()) / len(scores) if scores else 0.0

        return EvalResult(
            case_id=case["id"],
            description=case["description"],
            passed=overall_score >= 0.7,
            overall_score=overall_score,
            dimension_scores=scores,
            latency_ms=latency_ms,
            errors=errors,
            final_state_summary={
                "risk_level": str(final_state.get("final_risk_level")),
                "fraud_score": final_state.get("final_fraud_score"),
                "escalation_status": str(final_state.get("escalation_status")),
                "agents_completed": final_state.get("agents_completed", []),
            }
        )

    except Exception as e:
        logger.error(f"[EVAL] Case {case['id']} failed: {e}")
        return EvalResult(
            case_id=case["id"],
            description=case["description"],
            passed=False,
            overall_score=0.0,
            dimension_scores={},
            latency_ms=time.time() * 1000 - start_ms,
            errors=[str(e)],
            final_state_summary={}
        )


async def run_all_evals(dataset_path: str, output_path: str = None):
    """Run all eval cases and produce a summary report."""
    dataset = json.loads(Path(dataset_path).read_text())
    logger.info(f"[EVAL] Running {len(dataset)} eval cases")

    results = []
    for case in dataset:
        logger.info(f"[EVAL] Running {case['id']}: {case['description']}")
        result = await run_single_eval(case)
        results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        logger.info(f"[EVAL] {case['id']}: {status} | score={result.overall_score:.2f} | latency={result.latency_ms:.0f}ms")

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_score = sum(r.overall_score for r in results) / total
    avg_latency = sum(r.latency_ms for r in results) / total

    summary = {
        "run_timestamp": datetime.utcnow().isoformat(),
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3),
        "average_score": round(avg_score, 3),
        "average_latency_ms": round(avg_latency, 1),
        "results": [r.__dict__ for r in results]
    }

    print("\n" + "="*60)
    print(f"EVAL SUMMARY: {passed}/{total} passed ({100*passed/total:.0f}%)")
    print(f"Average score: {avg_score:.2f} | Average latency: {avg_latency:.0f}ms")
    print("="*60)

    if output_path:
        Path(output_path).write_text(json.dumps(summary, indent=2))
        logger.info(f"[EVAL] Results written to {output_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM evaluation suite")
    parser.add_argument("--dataset", default="evals/eval_dataset.json")
    parser.add_argument("--output", default="evals/results.json")
    args = parser.parse_args()

    asyncio.run(run_all_evals(args.dataset, args.output))

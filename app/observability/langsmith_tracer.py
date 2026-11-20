"""
langsmith_tracer.py
===================
LAYER: Observability — LangSmith Tracing

Decorator that wraps every agent node with LangSmith tracing.
Captures: agent name, latency, input state, output state, errors.
Every agent function uses @trace_agent("agent_name").
"""

import time
import logging
import functools
from typing import Callable
from langsmith import traceable
from app.config import settings
import os

logger = logging.getLogger(__name__)

# Set LangSmith env vars from config
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint


def trace_agent(agent_name: str):
    """
    Decorator for LangGraph agent nodes.
    Wraps the node function with LangSmith tracing + latency logging.

    Usage:
        @trace_agent("fraud_agent")
        async def fraud_agent_node(state: AgentState) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(state: dict, *args, **kwargs) -> dict:
            start_ms = time.time() * 1000
            logger.info(f"[TRACER] Starting agent: {agent_name} | session={state.get('session_id', 'N/A')}")

            try:
                # Wrap with LangSmith traceable
                traced_func = traceable(
                    name=agent_name,
                    run_type="chain",
                    project_name=settings.langchain_project
                )(func)

                result = await traced_func(state, *args, **kwargs)
                latency = time.time() * 1000 - start_ms
                logger.info(f"[TRACER] {agent_name} completed in {latency:.1f}ms")
                return result

            except Exception as e:
                latency = time.time() * 1000 - start_ms
                logger.error(f"[TRACER] {agent_name} failed after {latency:.1f}ms: {e}")
                # Return error state — graph continues, escalation agent handles it
                return {
                    "error": f"{agent_name} failed: {str(e)}",
                    "agents_completed": [agent_name],
                    "mcp_tools_called": []
                }

        return wrapper
    return decorator

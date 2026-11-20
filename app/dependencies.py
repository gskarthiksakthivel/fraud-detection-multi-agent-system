"""
dependencies.py
===============
LAYER: FastAPI Dependency Injection

Shared dependencies injected into route handlers.
Keeps route handlers thin and testable.
"""

from app.memory.redis_state import state_manager
from app.rag.case_retriever import CaseRetriever


async def get_state_manager():
    return state_manager


async def get_case_retriever():
    return CaseRetriever()

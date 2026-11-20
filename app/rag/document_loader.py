"""
document_loader.py
==================
LAYER: RAG — Document Loader

Loads and embeds documents into ChromaDB.
Called by scripts/seed_vector_db.py on first setup.
"""

import logging
from app.rag.case_retriever import CaseRetriever
from app.rag.mock_documents import MOCK_FRAUD_CASES

logger = logging.getLogger(__name__)


async def seed_knowledge_base() -> int:
    """
    Seed ChromaDB with all mock fraud cases.
    Returns count of documents loaded.
    Idempotent — skips existing case IDs.
    """
    retriever = CaseRetriever()
    loaded = 0

    for case in MOCK_FRAUD_CASES:
        try:
            await retriever.add_case(
                case_id=case["case_id"],
                summary=case["summary"],
                metadata=case["metadata"]
            )
            loaded += 1
            logger.info(f"[LOADER] Loaded {case['case_id']}")
        except Exception as e:
            logger.warning(f"[LOADER] Skipped {case['case_id']}: {e}")

    logger.info(f"[LOADER] Seeded {loaded}/{len(MOCK_FRAUD_CASES)} cases")
    return loaded

"""
seed_vector_db.py
=================
One-command ChromaDB seeding.
Run this on first setup: python scripts/seed_vector_db.py

Loads all 20 mock fraud cases from app/rag/mock_documents.py
into the ChromaDB fraud_cases collection.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    from app.rag.document_loader import seed_knowledge_base

    logger.info("Seeding ChromaDB with fraud case documents...")
    count = await seed_knowledge_base()
    logger.info(f"Done! {count} documents loaded into ChromaDB.")
    logger.info("You can now run the investigation agent with RAG retrieval.")


if __name__ == "__main__":
    asyncio.run(main())

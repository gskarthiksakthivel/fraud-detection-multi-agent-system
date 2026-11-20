"""
case_retriever.py
=================
LAYER: RAG — ChromaDB Case Retriever

Retrieves similar past fraud cases from ChromaDB vector store.
Used by investigation_agent to find pattern matches.

Embedding model: OpenAI text-embedding-3-small
Collection: fraud_cases (seeded by scripts/seed_vector_db.py)
"""

import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)


class CaseRetriever:
    """
    RAG retriever for fraud case documents.

    Each document in ChromaDB has:
      - id: case_id (e.g. "CASE-001")
      - document: case summary text
      - metadata: outcome, fraud_type, amount_range, country
    """

    def __init__(self):
        self._client: Optional[chromadb.AsyncHttpClient] = None
        self._collection = None
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key
        )

    async def _get_collection(self):
        if self._collection is None:
            self._client = await chromadb.AsyncHttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
            self._collection = await self._client.get_or_create_collection(
                name=settings.chroma_collection,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    async def retrieve(self, query: str, k: int = 5) -> List[dict]:
        """
        Retrieve top-k similar fraud cases for a query.
        Returns list of {case_id, summary, outcome, similarity_score}.
        """
        try:
            collection = await self._get_collection()
            query_embedding = await self._embeddings.aembed_query(query)

            results = await collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, 20),
                include=["documents", "metadatas", "distances"]
            )

            cases = []
            if results and results.get("ids") and results["ids"][0]:
                for i, case_id in enumerate(results["ids"][0]):
                    cases.append({
                        "case_id": case_id,
                        "summary": results["documents"][0][i],
                        "outcome": results["metadatas"][0][i].get("outcome", "UNKNOWN"),
                        "fraud_type": results["metadatas"][0][i].get("fraud_type", "UNKNOWN"),
                        "similarity_score": round(1 - results["distances"][0][i], 3)
                    })

            logger.info(f"[RAG] Retrieved {len(cases)} cases for query: {query[:80]}")
            return cases

        except Exception as e:
            logger.error(f"[RAG] Retrieval failed: {e}")
            return []

    async def add_case(self, case_id: str, summary: str, metadata: dict) -> None:
        """Add a new fraud case to the knowledge base."""
        collection = await self._get_collection()
        embedding = await self._embeddings.aembed_query(summary)
        await collection.add(
            ids=[case_id],
            embeddings=[embedding],
            documents=[summary],
            metadatas=[metadata]
        )
        logger.info(f"[RAG] Added case {case_id} to knowledge base")

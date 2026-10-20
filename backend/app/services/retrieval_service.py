import logging
from typing import Any, Dict, List, Optional
from app.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Coordinates semantic vector retrieval with strict user isolation,
    document boundary filtering, and relevance thresholding.
    """

    @property
    def vector_store(self):
        return get_vector_store()

    def retrieve_relevant_chunks(
        self,
        query: str,
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = settings.TOP_K_RESULTS,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Embeds the query and queries the vector store.
        Guarantees that chunks belonging to another owner are excluded.
        """
        if not query or not query.strip():
            return []

        # Generate query vector
        query_vector = embedding_service.embed_query(query)

        # Execute isolated vector search
        chunks = self.vector_store.search(
            query_embedding=query_vector,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k,
            min_score=min_score
        )

        logger.info(
            "Retrieved %d chunks for user %s (query length %d, docs filtered: %s)",
            len(chunks), owner_id, len(query), bool(document_ids)
        )
        return chunks


retrieval_service = RetrievalService()

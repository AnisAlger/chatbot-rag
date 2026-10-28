import json
import logging
import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from app.config import settings
from app.database import db_manager

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """
    Abstract Vector Store interface supporting chunk indexing, semantic search, and cleanup.
    """

    @abstractmethod
    def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Indexes text chunks along with their vector embeddings."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic vector similarity search strictly bounded by owner_id and optional document_ids.
        Returns chunks sorted by descending cosine similarity.
        """
        pass

    @abstractmethod
    def get_document_chunks(
        self,
        owner_id: str,
        document_ids: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieves initial chunks of the specified document(s) for general queries."""
        pass

    @abstractmethod
    def delete_document_chunks(self, document_id: str, owner_id: str) -> int:
        """Deletes all vector chunks belonging to the specified document and owner."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic metadata about the vector store."""
        pass


class LocalVectorStore(BaseVectorStore):
    """
    High-performance, persistent local vector store using NumPy and JSON metadata.
    Provides complete offline vector search capability with true cosine similarity.
    """

    def __init__(self, store_path: str = settings.LOCAL_VECTOR_STORE_PATH):
        self.store_dir = Path(store_path)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.store_dir / "chunks_metadata.json"
        self.vectors_file = self.store_dir / "chunks_vectors.npy"

        self.chunks_metadata: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        self._load()

    def _load(self):
        try:
            if self.metadata_file.exists() and self.vectors_file.exists():
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.chunks_metadata = json.load(f)
                self.vectors = np.load(str(self.vectors_file))
                logger.info("Loaded %d vectors from local vector store at %s", len(self.chunks_metadata), self.store_dir)
            else:
                self.chunks_metadata = []
                self.vectors = None
        except Exception as e:
            logger.warning("Could not load local vector store (%s). Initializing empty store.", e)
            self.chunks_metadata = []
            self.vectors = None

    def _persist(self):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks_metadata, f, ensure_ascii=False)
            if self.vectors is not None:
                np.save(str(self.vectors_file), self.vectors)
        except Exception as e:
            logger.error("Failed to persist local vector store: %s", e)

    def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        if not chunks or not embeddings:
            return

        new_vectors = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_vectors = new_vectors / norms

        if self.vectors is None or len(self.chunks_metadata) == 0:
            self.vectors = normalized_vectors
            self.chunks_metadata = list(chunks)
        else:
            self.vectors = np.vstack([self.vectors, normalized_vectors])
            self.chunks_metadata.extend(chunks)

        self._persist()

    def search(
        self,
        query_embedding: List[float],
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if self.vectors is None or len(self.chunks_metadata) == 0:
            return []

        allowed_indices = []
        doc_set = set(document_ids) if document_ids else None

        for idx, meta in enumerate(self.chunks_metadata):
            if meta.get("owner_id") != owner_id:
                continue
            if doc_set is not None and meta.get("document_id") not in doc_set:
                continue
            allowed_indices.append(idx)

        if not allowed_indices:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        candidate_vectors = self.vectors[allowed_indices]
        scores = np.dot(candidate_vectors, q_vec)

        ranked_order = np.argsort(scores)[::-1]

        results = []
        for rank in ranked_order:
            score = float(scores[rank])
            if score < min_score:
                continue
            orig_idx = allowed_indices[rank]
            chunk_data = dict(self.chunks_metadata[orig_idx])
            chunk_data["score"] = round(score, 4)
            results.append(chunk_data)
            if len(results) >= top_k:
                break

        return results

    def get_document_chunks(
        self,
        owner_id: str,
        document_ids: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        doc_set = set(document_ids) if document_ids else None
        results = []
        for meta in self.chunks_metadata:
            if meta.get("owner_id") != owner_id:
                continue
            if doc_set is not None and meta.get("document_id") not in doc_set:
                continue
            results.append(dict(meta))

        results.sort(key=lambda x: (x.get("page_number", 1), x.get("chunk_index", 0)))
        return results[:limit]

    def delete_document_chunks(self, document_id: str, owner_id: str) -> int:
        if self.vectors is None or len(self.chunks_metadata) == 0:
            return 0

        keep_indices = []
        deleted_count = 0

        for idx, meta in enumerate(self.chunks_metadata):
            if meta.get("document_id") == document_id and meta.get("owner_id") == owner_id:
                deleted_count += 1
            else:
                keep_indices.append(idx)

        if deleted_count > 0:
            if keep_indices:
                self.chunks_metadata = [self.chunks_metadata[i] for i in keep_indices]
                self.vectors = self.vectors[keep_indices]
            else:
                self.chunks_metadata = []
                self.vectors = None
            self._persist()

        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        return {
            "type": "local_numpy",
            "total_vectors": len(self.chunks_metadata),
            "storage_path": str(self.store_dir)
        }


class MongoAtlasVectorStore(BaseVectorStore):
    """
    MongoDB Atlas Vector Search adapter using Atlas Search ($vectorSearch)
    with seamless in-database cosine similarity fallback when Atlas Search index
    is not configured or returns empty results.
    """

    def __init__(self, index_name: str = settings.MONGODB_VECTOR_INDEX_NAME):
        self.index_name = index_name
        self.fallback = LocalVectorStore()

    def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        if db_manager.is_fallback:
            self.fallback.insert_chunks(chunks, embeddings)
            return

        docs_to_insert = []
        for chunk, emb in zip(chunks, embeddings):
            doc = dict(chunk)
            doc["embedding"] = emb
            docs_to_insert.append(doc)

        if docs_to_insert:
            try:
                db_manager.chunks.insert_many(docs_to_insert)
            except Exception as e:
                logger.error("Failed to insert chunks to MongoDB: %s", e)
                self.fallback.insert_chunks(chunks, embeddings)

    def search(
        self,
        query_embedding: List[float],
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if db_manager.is_fallback:
            return self.fallback.search(query_embedding, owner_id, document_ids, top_k, min_score)

        # 1. Try native Atlas $vectorSearch if available
        filter_clause: Dict[str, Any] = {"owner_id": {"$eq": owner_id}}
        if document_ids:
            filter_clause["document_id"] = {"$in": document_ids}

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(50, top_k * 10),
                    "limit": top_k,
                    "filter": filter_clause
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "embedding": 0,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            cursor = db_manager.chunks.aggregate(pipeline)
            results = list(cursor)
            filtered = [r for r in results if r.get("score", 1.0) >= min_score]
            if filtered:
                return filtered
        except Exception as e:
            logger.info("Atlas $vectorSearch not configured or failed (%s). Using MongoDB in-database vector fallback.", e)

        # 2. Resilient fallback: compute exact cosine similarity over user chunks directly from MongoDB
        return self._search_mongodb_in_memory(query_embedding, owner_id, document_ids, top_k, min_score)

    def _search_mongodb_in_memory(
        self,
        query_embedding: List[float],
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        filter_query: Dict[str, Any] = {"owner_id": owner_id}
        if document_ids:
            filter_query["document_id"] = {"$in": document_ids}

        try:
            candidates = list(db_manager.chunks.find(filter_query))
        except Exception as e:
            logger.error("Failed to query chunks from MongoDB: %s", e)
            return self.fallback.search(query_embedding, owner_id, document_ids, top_k, min_score)

        if not candidates:
            # Check local file fallback if legacy chunks exist
            return self.fallback.search(query_embedding, owner_id, document_ids, top_k, min_score)

        vectors = []
        valid_candidates = []
        for c in candidates:
            emb = c.get("embedding")
            if emb and isinstance(emb, list) and len(emb) == len(query_embedding):
                vectors.append(emb)
                valid_candidates.append(c)

        if not valid_candidates:
            return self.fallback.search(query_embedding, owner_id, document_ids, top_k, min_score)

        matrix = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_matrix = matrix / norms

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = np.dot(normalized_matrix, q_vec)
        ranked = np.argsort(scores)[::-1]

        results = []
        for rank in ranked:
            score = float(scores[rank])
            if score < min_score:
                continue
            item = dict(valid_candidates[rank])
            item.pop("_id", None)
            item.pop("embedding", None)
            item["score"] = round(score, 4)
            results.append(item)
            if len(results) >= top_k:
                break

        return results

    def get_document_chunks(
        self,
        owner_id: str,
        document_ids: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not db_manager.is_fallback:
            try:
                filter_q: Dict[str, Any] = {"owner_id": owner_id}
                if document_ids:
                    filter_q["document_id"] = {"$in": document_ids}

                cursor = db_manager.chunks.find(
                    filter_q,
                    {"_id": 0, "embedding": 0}
                ).sort([("page_number", 1), ("chunk_index", 1)]).limit(limit)
                chunks = list(cursor)
                if chunks:
                    return chunks
            except Exception as e:
                logger.error("Error retrieving document chunks from MongoDB: %s", e)

        return self.fallback.get_document_chunks(owner_id, document_ids, limit)

    def delete_document_chunks(self, document_id: str, owner_id: str) -> int:
        count = 0
        if not db_manager.is_fallback:
            try:
                res = db_manager.chunks.delete_many({"document_id": document_id, "owner_id": owner_id})
                count += res.deleted_count
            except Exception as e:
                logger.error("Failed to delete chunks from MongoDB: %s", e)
        count += self.fallback.delete_document_chunks(document_id, owner_id)
        return count

    def get_stats(self) -> Dict[str, Any]:
        mongo_chunk_count = 0
        if not db_manager.is_fallback:
            try:
                mongo_chunk_count = db_manager.chunks.count_documents({})
            except Exception:
                pass

        return {
            "type": "mongodb_atlas",
            "index_name": self.index_name,
            "connected": not db_manager.is_fallback,
            "total_chunks_in_mongo": mongo_chunk_count,
            "fallback_stats": self.fallback.get_stats()
        }


# Global vector store instance
_vector_store: Optional[BaseVectorStore] = None


def get_vector_store() -> BaseVectorStore:
    global _vector_store
    if _vector_store is None:
        if settings.VECTOR_STORE_TYPE.lower() == "atlas" or not db_manager.is_fallback:
            _vector_store = MongoAtlasVectorStore()
        else:
            _vector_store = LocalVectorStore()
    return _vector_store

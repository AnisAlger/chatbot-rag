import hashlib
import logging
import math
from typing import List, Optional
import httpx
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class BaseEmbeddingProvider:
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class OpenRouterEmbeddingProvider(BaseEmbeddingProvider):
    """
    Embedding provider using OpenRouter or any OpenAI-compatible embeddings endpoint.
    """
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise EmbeddingError(
                "Embedding API key is not configured. Set EMBEDDING_API_KEY or OPENROUTER_API_KEY in your environment."
            )
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=30.0,
                max_retries=2
            )
            # Truncate texts to ~350 tokens (1400 chars) to stay safely within embedding model token limits
            safe_inputs = [t[:1400] for t in texts]
            response = client.embeddings.create(
                model=self.model,
                input=safe_inputs
            )
            # Maintain index order
            embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
            return embeddings
        except Exception as e:
            logger.error("Embedding API request failed: %s", str(e))
            raise EmbeddingError(f"Failed to generate embeddings via provider: {str(e)}")


class LocalMockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-semantic embedding generator for offline testing and local development.
    Uses token hashing with non-negative frequency weights to guarantee positive cosine
    similarity for overlapping terms.
    """
    def __init__(self, dim: int = 256):
        self.dim = dim

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            vec = [0.0] * self.dim
            words = [w.strip(".,!?:;\"'()[]{}").lower() for w in text.split()]
            words = [w for w in words if len(w) > 1]
            if not words:
                embeddings.append(vec)
                continue

            for word in words:
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
                idx = h % self.dim
                vec[idx] += 1.0

            # Unit normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings


class EmbeddingService:
    """
    Orchestrates embedding generation with caching, batching, and provider abstraction.
    """
    def __init__(self):
        self._provider: Optional[BaseEmbeddingProvider] = None
        self._cache: dict = {}  # text_hash -> embedding

    def _get_provider(self) -> BaseEmbeddingProvider:
        if self._provider is not None:
            return self._provider

        provider_name = settings.EMBEDDING_PROVIDER.lower()
        api_key = settings.EMBEDDING_API_KEY or settings.OPENROUTER_API_KEY

        if provider_name in ("openrouter", "openai"):
            if not api_key:
                logger.warning("No EMBEDDING_API_KEY provided. Falling back to local_mock embedding provider.")
                self._provider = LocalMockEmbeddingProvider()
            else:
                self._provider = OpenRouterEmbeddingProvider(
                    api_key=api_key,
                    base_url=settings.EMBEDDING_BASE_URL,
                    model=settings.EMBEDDING_MODEL
                )
        else:
            self._provider = LocalMockEmbeddingProvider()

        return self._provider

    def set_provider(self, provider: BaseEmbeddingProvider):
        """Allows injecting custom or test providers."""
        self._provider = provider

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts, utilizing an in-memory cache to avoid redundant external calls.
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            thash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if thash in self._cache:
                results[i] = self._cache[thash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            provider = self._get_provider()
            # Batch in blocks of 50
            batch_size = 50
            for b in range(0, len(uncached_texts), batch_size):
                sub_texts = uncached_texts[b:b+batch_size]
                sub_embeddings = provider.get_embeddings(sub_texts)
                for j, emb in enumerate(sub_embeddings):
                    orig_idx = uncached_indices[b + j]
                    results[orig_idx] = emb
                    thash = hashlib.sha256(uncached_texts[b + j].encode("utf-8")).hexdigest()
                    self._cache[thash] = emb

        return [r for r in results if r is not None]

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a single query string.
        """
        embs = self.embed_texts([query])
        if not embs:
            raise EmbeddingError("Failed to generate embedding for query.")
        return embs[0]


embedding_service = EmbeddingService()

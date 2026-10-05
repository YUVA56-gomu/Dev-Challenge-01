from abc import ABC, abstractmethod
from typing import List
import numpy as np

try:
    from fastembed import TextEmbedding
    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass


class FastEmbedEmbeddingProvider(BaseEmbeddingProvider):
    """Local ONNX FastEmbed embedding provider using BAAI/bge-small-en-v1.5 (384d)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None and HAS_FASTEMBED:
            try:
                self._model = TextEmbedding(self.model_name)
            except Exception as e:
                print(f"[FastEmbedProvider] Warning initializing model: {e}")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model is None:
            # Fallback zero vector
            return [[0.0] * 384 for _ in texts]
        embeddings = list(model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> List[float]:
        model = self._get_model()
        if model is None:
            return [0.0] * 384
        embeddings = list(model.query_embed(query))
        return embeddings[0].tolist() if embeddings else [0.0] * 384


def get_embedding_provider() -> BaseEmbeddingProvider:
    return FastEmbedEmbeddingProvider()

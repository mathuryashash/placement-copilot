"""
Embedding service using fastembed (BAAI/bge-small-en-v1.5, ONNX, no torch).

The model is downloaded once to HF_HOME and reused across requests.
"""
from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Return L2-normalized embeddings for a list of texts."""
    model = _get_model()
    embeddings = list(model.embed(list(texts)))
    # fastembed returns numpy arrays; convert to Python lists for pgvector
    return [emb.tolist() for emb in embeddings]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]

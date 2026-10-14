"""
RAG 向量存储模块 - ChromaDB + Embedding
向量检索 -> 拼接上下文 -> LLM 生成
"""
import hashlib
import math

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.config import settings

EMBED_MODEL = "all-MiniLM-L6-v2"
DEFAULT_DIM = 384


def _hash_embedding(texts: list[str]) -> list[list[float]]:
    """Deterministic, dependency-free character-trigram hashing embedding.

    Same text -> same vector, always, offline. Used for smoke tests: it proves
    the wiring (load -> store -> retrieve) without downloading a model.
    It is NOT semantic -- cross-language or paraphrase queries will miss, so
    it must never be used for a capability claim.
    """
    out = []
    for text in texts:
        vec = [0.0] * DEFAULT_DIM
        padded = f" {text.lower()} "
        for i in range(len(padded) - 2):
            gram = padded[i:i + 3]
            slot = int(hashlib.md5(gram.encode()).hexdigest(), 16) % DEFAULT_DIM
            vec[slot] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        out.append([v / norm for v in vec])
    return out


def build_embedding_fn():
    """Pick an embedding function, most capable available one wins.

    Order (and why):
      1. sentence-transformers  -- best quality, needs torch (~800MB)
      2. chromadb default       -- ONNX runtime, downloads ~80MB model on first use
      3. hash embedding         -- offline, deterministic, non-semantic

    Returns (embedding_function_or_callable, name). `name` is recorded so a
    caller can state which one produced a result; comparing across encoders
    is not meaningful.
    """
    try:
        fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        fn(["probe"])
        return fn, "sentence-transformers"
    except Exception:
        pass
    try:
        fn = embedding_functions.DefaultEmbeddingFunction()
        fn(["probe"])
        return fn, "chromadb-default"
    except Exception:
        return _hash_embedding, "hash-trigram"


class VectorStore:
    def __init__(self, collection_name: str = "knowledge_base", embedding_fn=None):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        if embedding_fn is None:
            embedding_fn, self.embedding_name = build_embedding_fn()
        else:
            self.embedding_name = "injected"
        self.embedding_fn = embedding_fn
        # chroma validates the type of `embedding_function`, so a plain callable
        # (the deterministic fallback) cannot be registered here. For that path
        # the collection is created without one and every add/query passes
        # explicit embeddings instead.
        if self._is_hash():
            self.collection = self.client.get_or_create_collection(name=collection_name)
        else:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )

    def _is_hash(self) -> bool:
        """True when the embedding function is a plain callable (deterministic fallback).

        Deliberately name-based, not isinstance: chroma's EmbeddingFunction is a
        runtime-checkable Protocol, so isinstance() accepts any callable and
        would send a plain function down the chroma-validation path.
        """
        return self.embedding_name in ("hash-trigram", "injected")

    def add_documents(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        if ids is None:
            ids = [str(hash(t)) for t in texts]
        # chroma's injected-callable path still needs a real embedding at add time;
        # the deterministic fallback is applied here too so add and query agree.
        if self._is_hash():
            embeddings = self.embedding_fn(texts)
            self.collection.add(documents=texts,
                                embeddings=embeddings,
                                metadatas=metadatas or [{}] * len(texts),
                                ids=ids)
            return len(texts)
        self.collection.add(documents=texts, metadatas=metadatas or [{}] * len(texts), ids=ids)
        return len(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self._is_hash():
            embedding = self.embedding_fn([query])
            results = self.collection.query(query_embeddings=embedding,
                                            n_results=top_k)
        else:
            results = self.collection.query(query_texts=[query], n_results=top_k)
        docs = []
        for i in range(len(results["documents"][0])):
            docs.append({
                "content": results["documents"][0][i],
                "metadata": results.get("metadatas", [[{}]])[0][i],
                "distance": results.get("distances", [[0]])[0][i]
            })
        return docs

    def count(self) -> int:
        return self.collection.count()

"""ChromaDB 向量存储 - RAG 核心"""
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

class VectorStore:
    """向量数据库: ChromaDB 持久化存储 + 向量检索"""

    def __init__(self, collection: str = "knowledge_base"):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection)

    def add(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None) -> int:
        if not texts:
            return 0
        if ids is None:
            ids = [self._hash(t)[:12] for t in texts]
        if metadatas is None:
            metadatas = [{}] * len(texts)
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        return len(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        docs = []
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[{}]])[0]
        dists_list = results.get("distances", [[0]])[0]
        for i, doc in enumerate(docs_list):
            docs.append({"content": doc[:800], "metadata": metas_list[i], "distance": round(dists_list[i], 4)})
        return docs

    def delete(self, ids: list[str]):
        self.collection.delete(ids=ids)

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        ids = self.collection.get()["ids"]
        if ids:
            self.collection.delete(ids=ids)

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()

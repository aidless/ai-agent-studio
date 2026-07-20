"""
RAG 向量存储模块 - ChromaDB + Embedding
向量检索 -> 拼接上下文 -> LLM 生成
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.config import settings


class VectorStore:
    def __init__(self, collection_name: str = "knowledge_base"):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_documents(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        if ids is None:
            ids = [str(hash(t)) for t in texts]
        self.collection.add(documents=texts, metadatas=metadatas or [{}] * len(texts), ids=ids)
        return len(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
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

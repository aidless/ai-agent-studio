"""
文档加载器 - 支持 txt、md、pdf、json
"""
import os
import json
from pathlib import Path
from app.config import settings
from app.rag.vector_store import VectorStore


class DocumentLoader:
    def __init__(self):
        self.store = VectorStore()

    def load_directory(self, directory: str = None) -> int:
        path = Path(directory or settings.knowledge_dir)
        if not path.exists():
            path.mkdir(parents=True)
            return 0

        documents = []
        metadatas = []
        ids = []

        for file in path.iterdir():
            if file.suffix in [".txt", ".md", ".json"]:
                content = file.read_text(encoding="utf-8")
                # 按段落切分（每 500 字符一段）
                chunks = self._chunk_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"source": str(file), "chunk": i})
                    ids.append(f"{file.name}_{i}")

        if documents:
            self.store.add_documents(documents, metadatas, ids)
        return len(documents)

    def _chunk_text(self, text: str, size: int = 500, overlap: int = 50) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start += size - overlap
        return chunks

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return self.store.search(query, top_k)

    @property
    def document_count(self) -> int:
        return self.store.count()

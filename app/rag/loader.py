"""文档加载器 - 支持 txt/md/json/py/html 文件"""
import os
from pathlib import Path
from app.config import settings
from app.rag.store import VectorStore

class DocumentLoader:
    """从目录加载文档 -> 分块 -> 入库"""

    def __init__(self):
        self.store = VectorStore()

    def load_directory(self, directory: str = None) -> int:
        path = Path(directory or settings.knowledge_dir)
        if not path.exists():
            path.mkdir(parents=True)
            return 0

        total = 0
        for file in path.iterdir():
            if file.suffix.lower() in [".md", ".txt", ".py", ".json", ".html"]:
                try:
                    content = file.read_text(encoding="utf-8", errors="ignore")
                    chunks = self._smart_chunk(content, file.suffix)
                    ids = [f"{file.stem}_chunk{i}" for i in range(len(chunks))]
                    metas = [{"source": str(file), "chunk": i, "type": file.suffix} for i in range(len(chunks))]
                    self.store.add(chunks, metas, ids)
                    total += len(chunks)
                except Exception as e:
                    print(f"[WARN] 加载失败 {file}: {e}")
        return total

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return self.store.search(query, top_k)

    @property
    def count(self) -> int:
        return self.store.count()

    def _smart_chunk(self, text: str, ext: str, max_size: int = 600, overlap: int = 80) -> list[str]:
        """智能分块: 按段落、代码块、或固定大小切分"""
        chunks = []
        # 按双换行分段落
        paragraphs = text.split("\n\n")
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= max_size:
                current += ("\n\n" if current else "") + para
            else:
                if current:
                    chunks.append(current)
                # 如果单个段落超长，按句子或固定大小再切
                if len(para) > max_size:
                    for i in range(0, len(para), max_size - overlap):
                        chunks.append(para[i:i + max_size])
                else:
                    current = para
        if current:
            chunks.append(current)
        return chunks if chunks else [text[:max_size]]

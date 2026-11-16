#!/usr/bin/env python3
"""Benchmark the RAG wiring path with the deterministic hash encoder.

Plumbing timing only. It loads data/knowledge with the hash-trigram encoder,
writes one shot to results/bench-hash.json, and does not score relevance.
Recompute with `python3 bench_rag_wiring.py`. Seconds are not a spec.
"""
import json
import os
import platform
import time
import tempfile
from pathlib import Path

from app.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import _hash_embedding

ROOT = Path(__file__).resolve().parent


def main():
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        settings.chroma_persist_dir = td
        loader = DocumentLoader(embedding_fn=_hash_embedding)
        t_load0 = time.perf_counter()
        n_chunks = loader.load_directory()
        t_load = time.perf_counter() - t_load0

        # Indexing happens inside load_directory. There is no separate index timer.
        t_search0 = time.perf_counter()
        results = loader.search("RAG 是什么", top_k=5)
        t_search = time.perf_counter() - t_search0

        # determinism probe: same text twice must give same vector
        from app.rag.vector_store import _hash_embedding as _he
        v1 = _he(["RAG 是什么"])[0]
        v2 = _he(["RAG 是什么"])[0]
        deterministic = v1 == v2
        import math
        norm = math.sqrt(sum(x * x for x in v1))

    knowledge = Path(settings.knowledge_dir)
    n_docs = len([p for p in knowledge.iterdir() if p.suffix == ".md"]) if knowledge.is_dir() else 0
    stats = {
        "encoder": "hash-trigram",
        "n_docs": n_docs,
        "n_chunks": n_chunks,
        "top_k": len(results),
        "load_seconds": round(t_load, 4),
        "search_seconds": round(t_search, 4),
        "total_seconds": round(time.perf_counter() - t0, 4),
        "deterministic": deterministic,
        "l2_norm": round(norm, 6),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "note": "One shot on this process. Hash encoder is NON-SEMANTIC; timings are not a performance spec and do not measure quality.",
    }
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "bench-hash.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"-> {out_dir / 'bench-hash.json'}")


if __name__ == "__main__":
    main()

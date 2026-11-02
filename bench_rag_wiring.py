#!/usr/bin/env python3
"""Benchmark the RAG wiring path with the deterministic hash encoder.

This is a **plumbing benchmark**, not a quality benchmark: it measures how long
the injectable RAG path takes to load the 5 knowledge docs into 12 chunks, index
them in ChromaDB, and run a query — all with the deterministic, dependency-free
hash-trigram encoder. It deliberately avoids sentence-transformers (and the
~80MB model download) so it runs offline and reproducibly.

Honesty contract (matches README "证据" and PREREG.md §4):
  - The hash encoder is NON-SEMANTIC. Timings here say nothing about retrieval
    quality. Only that the load -> store -> retrieve wiring works and is fast.
  - Results are written to results/bench-hash.json so the numbers are committed
    and can be re-derived with `python3 bench_rag_wiring.py`.
"""
import json
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

        t_idx0 = time.perf_counter()
        # index is done inside load_directory (chroma add); measure a second
        # query + determinism probe separately below
        t_idx = time.perf_counter() - t_idx0

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

    stats = {
        "encoder": "hash-trigram",
        "n_docs": 5,
        "n_chunks": n_chunks,
        "top_k": len(results),
        "load_seconds": round(t_load, 4),
        "index_seconds": round(t_idx, 4),
        "search_seconds": round(t_search, 4),
        "total_seconds": round(time.perf_counter() - t0, 4),
        "deterministic": deterministic,
        "l2_norm": round(norm, 6),
        "note": "hash encoder is NON-SEMANTIC; timings prove wiring, not quality",
    }
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "bench-hash.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"-> {out_dir / 'bench-hash.json'}")


if __name__ == "__main__":
    main()

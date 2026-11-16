#!/usr/bin/env python3
"""Negative retrieval check for the hash-trigram encoder.

This is not a preregistration. The rule below is a consequence of the
encoder in app/rag/vector_store.py: a vector is a bag of character
trigrams. The English sentence PARA_EN was chosen so that it shares no
trigram with SEM. When that overlap is 0, a nearest-neighbor hit is not
evidence of semantic retrieval.

Gate (cosine ceiling 0.5): an exact copy has cosine 1. A zero-overlap
paraphrase must stay under 0.5. The measured cosine is an output, stored
in results/negative-hash.json, not a target to tune.

`--onnx` records one extra pair on Chroma's default embedder. That probe
downloads a model on first use and is not part of `make check`.

Exit 0 when the hash gate holds and the committed snapshot matches.
Exit 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HASH_PATH = REPO / "results" / "negative-hash.json"
ONNX_PATH = REPO / "results" / "negative-onnx.json"
HASHES_PATH = REPO / "results" / "knowledge-sha256.json"

SEM = "研究员在回答之前检索知识库。"
LEX = "banana banana lexical marker"
PARA_ZH = "分析员会先查资料再作答。"
PARA_EN = "An analyst looks up notes first and then replies."
UNRELATED = "量子光合作用食谱"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _trigrams(text: str) -> set[str]:
    padded = f" {text.lower()} "
    return {padded[i:i + 3] for i in range(len(padded) - 2)}


def _dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def knowledge_hashes() -> dict:
    files = {}
    for path in sorted((REPO / "data" / "knowledge").iterdir()):
        if path.is_file():
            rel = path.relative_to(REPO).as_posix()
            files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"algorithm": "sha256", "files": files}


def _ranked(hits: list[dict]) -> list[dict]:
    ranked = []
    for hit in hits:
        source = str(hit.get("metadata", {}).get("source", ""))
        ranked.append({
            "distance": round(float(hit.get("distance", 0.0)), 4),
            "source": Path(source).name,
        })
    return ranked


def _cosine(embed, left: str, right: str) -> float:
    a = embed([left])[0]
    b = embed([right])[0]
    return float(sum(x * y for x, y in zip(a, b)))


def run_hash_probe() -> dict:
    from app.config import settings
    from app.rag.document_loader import DocumentLoader
    from app.rag.vector_store import _hash_embedding

    old_chroma = settings.chroma_persist_dir
    old_knowledge = settings.knowledge_dir
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notes = root / "notes"
            notes.mkdir()
            (notes / "sem.md").write_text(SEM, encoding="utf-8")
            (notes / "lex.md").write_text(LEX, encoding="utf-8")
            settings.chroma_persist_dir = str(root / "chroma")
            settings.knowledge_dir = str(notes)
            loader = DocumentLoader(embedding_fn=_hash_embedding)
            n_chunks = loader.load_directory()
            queries = {
                "exact_sem": SEM,
                "exact_lex": LEX,
                "para_zh": PARA_ZH,
                "para_en": PARA_EN,
            }
            recorded = {}
            for name, query in queries.items():
                ranked = _ranked(loader.search(query, top_k=2))
                recorded[name] = {
                    "query": query,
                    "ranked": ranked,
                    "top1": ranked[0]["source"] if ranked else "",
                }
    finally:
        settings.chroma_persist_dir = old_chroma
        settings.knowledge_dir = old_knowledge

    overlap_en = len(_trigrams(PARA_EN) & _trigrams(SEM))
    overlap_zh = len(_trigrams(PARA_ZH) & _trigrams(SEM))
    cosine_en = round(_cosine(_hash_embedding, PARA_EN, SEM), 6)
    cosine_zh = round(_cosine(_hash_embedding, PARA_ZH, SEM), 6)
    top_en = recorded["para_en"]["top1"]
    if overlap_en == 0 and top_en != "sem.md":
        conclusion = (
            "PARA_EN shares no character trigram with SEM, and its nearest "
            f"neighbor was {top_en}, not sem.md. Semantic retrieval is not supported."
        )
    elif overlap_en == 0:
        conclusion = (
            "PARA_EN shares no character trigram with SEM. A nearest-neighbor "
            "hit on sem.md would be a hash collision or a tie, not semantic retrieval."
        )
    else:
        conclusion = "Probe invalid: PARA_EN overlaps SEM, so this pair cannot support the negative claim."
    return {
        "chunks_loaded": n_chunks,
        "conclusion": conclusion,
        "documents": {"lex.md": LEX, "sem.md": SEM},
        "encoder": "hash-trigram",
        "exact_sem_cosine": round(_cosine(_hash_embedding, SEM, SEM), 6),
        "gated": True,
        "para_en": PARA_EN,
        "para_en_cosine_with_sem": cosine_en,
        "para_en_trigram_overlap_with_sem": overlap_en,
        "para_zh": PARA_ZH,
        "para_zh_cosine_with_sem": cosine_zh,
        "para_zh_trigram_overlap_with_sem": overlap_zh,
        "queries": recorded,
        "semantic_retrieval_supported": False if overlap_en == 0 else None,
    }


def assert_hash_report(report: dict) -> None:
    if report["chunks_loaded"] != 2:
        raise AssertionError(f"expected 2 chunks, got {report['chunks_loaded']}")
    if report["queries"]["exact_sem"]["top1"] != "sem.md":
        raise AssertionError(report["queries"]["exact_sem"])
    if report["queries"]["exact_lex"]["top1"] != "lex.md":
        raise AssertionError(report["queries"]["exact_lex"])
    if report["queries"]["exact_sem"]["ranked"][0]["distance"] != 0.0:
        raise AssertionError(report["queries"]["exact_sem"]["ranked"])
    if report["para_en_trigram_overlap_with_sem"] != 0:
        raise AssertionError("PARA_EN unexpectedly shares trigrams with SEM; pick a new sentence")
    if not report["para_en_cosine_with_sem"] < 0.5:
        raise AssertionError(report["para_en_cosine_with_sem"])
    if report["exact_sem_cosine"] < 0.999:
        raise AssertionError(report["exact_sem_cosine"])
    if report["semantic_retrieval_supported"] is not False:
        raise AssertionError(report["semantic_retrieval_supported"])


def run_onnx_probe() -> dict:
    """One synthetic pair on the server embedder. Not a benchmark. Needs the model download."""
    import chromadb

    from app.config import settings
    from app.rag.store import VectorStore

    old_chroma = settings.chroma_persist_dir
    try:
        with tempfile.TemporaryDirectory() as tmp:
            settings.chroma_persist_dir = tmp
            store = VectorStore(collection="negative_onnx")
            store.add(
                [SEM, LEX],
                [{"source": "sem"}, {"source": "lex"}],
                ["sem", "lex"],
            )
            queries = {
                "exact_sem": SEM,
                "exact_lex": LEX,
                "para_zh": PARA_ZH,
                "para_en": PARA_EN,
                "unrelated": UNRELATED,
            }
            recorded = {}
            for name, query in queries.items():
                ranked = _ranked(store.search(query, top_k=2))
                recorded[name] = {
                    "query": query,
                    "ranked": ranked,
                    "top1": ranked[0]["source"] if ranked else "",
                }
    finally:
        settings.chroma_persist_dir = old_chroma

    zh = recorded["para_zh"]["top1"]
    en = recorded["para_en"]["top1"]
    return {
        "chromadb_version": chromadb.__version__,
        "conclusion": (
            "One synthetic pair on Chroma's default embedder (no embedding_function "
            f"passed). Chinese paraphrase top-1 was {zh}. English paraphrase top-1 was {en}. "
            "n=1 pair; do not generalize. An unrelated query still receives a neighbor "
            "because the index always returns one."
        ),
        "gated": False,
        "note": (
            "Not part of make check. First use downloads Chroma's ONNX model "
            "(about 79MB). On chromadb 0.5.23 that file was all-MiniLM-L6-v2."
        ),
        "queries": recorded,
    }


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the hash snapshot and knowledge hashes")
    parser.add_argument("--check", action="store_true", help="assert the hash gate and the committed snapshot")
    parser.add_argument("--onnx", action="store_true", help="rerun the ungated ONNX pair and rewrite its snapshot")
    args = parser.parse_args()
    if not (args.write or args.check or args.onnx):
        args.check = True

    if args.write or args.check:
        report = run_hash_probe()
        try:
            assert_hash_report(report)
        except AssertionError as exc:
            return _fail(f"hash gate failed: {exc}")
        hashes = knowledge_hashes()
        if args.write:
            _dump(HASH_PATH, report)
            _dump(HASHES_PATH, hashes)
            print(f"wrote {HASH_PATH.relative_to(REPO)}")
            print(f"wrote {HASHES_PATH.relative_to(REPO)}")
        if args.check:
            if not HASH_PATH.is_file() or not HASHES_PATH.is_file():
                return _fail("missing results snapshot; run with --write")
            saved = json.loads(HASH_PATH.read_text(encoding="utf-8"))
            saved_hashes = json.loads(HASHES_PATH.read_text(encoding="utf-8"))
            if saved != report:
                return _fail("results/negative-hash.json does not match a fresh run; run with --write")
            if saved_hashes != hashes:
                return _fail("results/knowledge-sha256.json does not match data/knowledge; run with --write")
            print("hash negative check passed (semantic retrieval not supported; exact copies rank first)")

    if args.onnx:
        onnx = run_onnx_probe()
        _dump(ONNX_PATH, onnx)
        print(onnx["conclusion"])
        print(f"wrote {ONNX_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

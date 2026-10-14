"""AI Agent Studio 功能测试

These are smoke scripts, not unit tests: they print and return None, so pytest collects
them but they cannot fail on a wrong answer. Do not read a green run here as
evidence the agents work -- the printouts are the evidence.

Import discipline: the application modules are imported INSIDE the test functions,
never at module level. The mutation-control job installs pytest only (it deliberately
avoids the application deps and the model download), so a module-level
`from app...` import makes collection fail there -- and the reverse control then dies
at its own baseline check for a reason that has nothing to do with the defect it is
trying to inject. Collection must depend on pytest alone.

Embedding: the RAG smoke path injects the deterministic hash encoder
(`app.rag.vector_store._hash_embedding`) instead of sentence-transformers /
the chromadb ONNX default. That keeps CI free of an ~80MB model download and
of torch, and makes the run reproducible. The encoder is non-semantic; a
result line here says nothing about retrieval quality.
"""
import os
import sys

import pytest

sys.path.insert(0, ".")


NEEDS_KEY = pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY unset: the agent path calls a real LLM, so it is skipped, not faked",
)


def _rag_smoke(tmp_dir, set_persist_dir):
    """Shared body of the RAG smoke check, so --main and pytest run one code path."""
    from app.config import settings
    from app.rag.document_loader import DocumentLoader
    from app.rag.vector_store import _hash_embedding

    print("=" * 50)
    print("测试 1: RAG 向量检索")
    print("=" * 50)
    set_persist_dir(tmp_dir)
    loader = DocumentLoader(embedding_fn=_hash_embedding)
    count = loader.load_directory()
    print(f"[OK] 加载 {count} 个文档片段到向量数据库")
    print(f"[OK] encoder: {loader.store.embedding_name}")

    results = loader.search("RAG 是什么")
    print(f"[OK] 检索到 {len(results)} 条相关文档")
    for r in results[:2]:
        print(f"  - {r['content'][:100]}...")
    print()


def test_rag(tmp_path, monkeypatch):
    from app.config import settings

    _rag_smoke(str(tmp_path / "chroma"),
               lambda d: monkeypatch.setattr(settings, "chroma_persist_dir", d))


def test_hash_embedding_is_deterministic_and_normalised():
    from app.rag.vector_store import _hash_embedding

    a = _hash_embedding(["同一段文字"])
    b = _hash_embedding(["同一段文字"])
    assert a == b
    assert len(a[0]) == 384
    norm = sum(v * v for v in a[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-6


# `task_type` and `content` were function parameters, so pytest read them as
# fixtures and the run died at collection with
#   ERROR tests/test_agents.py::test_agent
#   fixture 'task_type' not found
# These are smoke scripts driven from __main__ below, not isolated unit tests, so
# they take no arguments. If they are ever meant to run under pytest they need
# real assertions -- a test that only prints cannot fail on a wrong answer, which
# is why the suite above was already green while this one errored.
@NEEDS_KEY
def test_agent(task_type: str = "research",
               content: str = "AI Agent Studio 的 RAG 架构是什么样的？"):
    from app.agents.orchestrator import Orchestrator

    print("=" * 50)
    print(f"测试: Agent ({task_type})")
    print("=" * 50)
    orch = Orchestrator()
    result = orch.run(task_type, content)
    if "error" in result:
        print(f"[FAIL] {result['error']}")
    else:
        print(f"[OK] Agent: {result['agent']}")
        print(f"[输出] {result['result'][:500]}...")
    print()


if __name__ == "__main__":
    import tempfile

    from app.config import settings

    with tempfile.TemporaryDirectory() as td:
        settings.chroma_persist_dir = td
        _rag_smoke(td, lambda d: setattr(settings, "chroma_persist_dir", d))
    test_agent()
    test_agent("writer", "为 AI Agent Studio 项目生成一份项目日报")
    print("全部测试完成!")

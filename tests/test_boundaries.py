"""Boundaries the offline gate is allowed to claim.

Imports stay inside the tests so collection needs only pytest. The CI
mutation job collects this file without installing the application.
"""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _probe():
    path = REPO / "eval" / "negative_retrieval.py"
    spec = importlib.util.spec_from_file_location("negative_retrieval", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_version_label_is_unreleased():
    from app.config import settings

    assert settings.app_version == "0.3.0-dev"


def test_health_route_does_not_claim_healthy():
    text = (REPO / "app" / "api" / "routes.py").read_text(encoding="utf-8")
    assert '"healthy"' not in text
    assert "llm_probed" in text
    assert '"status": "up"' in text


def test_server_chunker_counts_eleven_notes():
    """app.rag.loader's chunker, without opening Chroma or downloading a model."""
    from app.rag.loader import DocumentLoader

    total = 0
    notes = REPO / "data" / "knowledge"
    for path in notes.iterdir():
        if path.suffix.lower() in [".md", ".txt", ".py", ".json", ".html"]:
            content = path.read_text(encoding="utf-8", errors="ignore")
            total += len(DocumentLoader._smart_chunk(None, content, path.suffix))
    assert total == 11


def test_empty_api_key_does_not_construct_a_client(monkeypatch):
    from openai import OpenAIError

    from app.agents.base import LLMFactory
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "")
    with pytest.raises(OpenAIError):
        LLMFactory.create()


def test_pipeline_reports_agent_error_strings():
    from app.agents.orchestrator import Orchestrator

    class Fake:
        name = "writer"

        def invoke(self, task):
            return "[Agent error] boom"

    orch = object.__new__(Orchestrator)
    orch._tasks = {"writer": Fake()}
    out = orch.pipeline("task", ["writer"])
    assert out["steps"] == []
    assert out["final_output"] == ""
    assert out["errors"] == [{"step": "writer", "error": "[Agent error] boom"}]


def test_hash_paraphrase_is_not_semantic_retrieval():
    probe = _probe()
    report = probe.run_hash_probe()
    probe.assert_hash_report(report)
    saved = probe.json.loads(probe.HASH_PATH.read_text(encoding="utf-8"))
    assert saved["semantic_retrieval_supported"] is False
    assert saved["para_en_trigram_overlap_with_sem"] == 0


def test_knowledge_hashes_match_the_tree():
    probe = _probe()
    saved = probe.json.loads(probe.HASHES_PATH.read_text(encoding="utf-8"))
    assert saved == probe.knowledge_hashes()


def test_v2_keyword_search_hits_a_fragment_and_misses_a_paraphrase():
    """agent_studio.RAGEngine counts whitespace tokens. It is not the hash path."""
    import agent_studio

    probe = _probe()
    engine = agent_studio.RAGEngine()
    engine.ingest(probe.SEM, {"source": "sem"})
    engine.ingest(probe.LEX, {"source": "lex"})
    fragment = engine.search("知识库")
    assert fragment and fragment[0]["metadata"]["source"] == "sem"
    # str.count("an") is 4 inside "banana banana", so the paraphrase false-hits
    # the unrelated note and does not hit the relevant one.
    paraphrase = engine.search(probe.PARA_EN)
    assert [hit["metadata"]["source"] for hit in paraphrase] == ["lex"]
    assert paraphrase[0]["score"] == 4

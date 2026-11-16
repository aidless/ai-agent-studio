# Claim ledger

Each row is something this repository either measured or refuses to claim.
"Supported" means the command fails if the statement breaks. It does not
mean the statement is a user-facing quality result.

Recompute the offline rows with `make check` after `pip install -r requirements-dev.txt`.
No API key.

| ID | Claim | Verdict | Check |
|---|---|---|---|
| C1 | Hash embedding is deterministic, length 384, L2 norm 1 | Supported | `pytest tests/test_agents.py::test_hash_embedding_is_deterministic_and_normalised` |
| C2 | Hash loader splits `data/knowledge` into 12 chunks and a query returns 5 neighbors | Supported as wiring. Not a relevance score. | `pytest tests/test_agents.py::test_rag` |
| C3 | Server chunker (`app.rag.loader._smart_chunk`) splits the same notes into 11 chunks | Supported. Does not open Chroma. | `pytest tests/test_boundaries.py::test_server_chunker_counts_eleven_notes` |
| C4 | Exact copy is the hash nearest neighbor at distance 0; `PARA_EN` shares 0 trigrams with that note and cosine is under 0.5, so semantic retrieval is not supported | Supported negative result | `python3 eval/negative_retrieval.py --check` |
| C5 | `agent_studio.py` keyword search hits the fragment `知识库`. `PARA_EN` misses that note and false-hits `lex` with score 4, because `an` occurs inside `banana` | Supported for that engine only | `pytest tests/test_boundaries.py::test_v2_keyword_search_hits_a_fragment_and_misses_a_paraphrase` |
| C6 | Unknown agent name returns `Unknown agent: nope` | Supported | eval case `ORC-01` |
| C7 | A step whose text starts with `[Agent error]` is listed in `pipeline.errors` and is not `final_output` | Supported for a fake agent. Not a live model call. | `pytest tests/test_boundaries.py::test_pipeline_reports_agent_error_strings` |
| C8 | Empty API key does not construct the chat client | Supported (`openai.OpenAIError`) | `pytest tests/test_boundaries.py::test_empty_api_key_does_not_construct_a_client` |
| C9 | `/health` does not say `healthy` and records `llm_probed` | Supported as a source check, not a live HTTP probe | `pytest tests/test_boundaries.py::test_health_route_does_not_claim_healthy` |
| C10 | In-code package version is `0.3.0-dev` | Supported. The string means unreleased. | `pytest tests/test_boundaries.py::test_version_label_is_unreleased` |
| C11 | Committed `data/chroma/chroma.sqlite3` has 0 embedding rows | Supported | eval case `CHR-01` |
| C12 | `data/knowledge` bytes match `results/knowledge-sha256.json` | Supported | `python3 eval/negative_retrieval.py --check` |
| C13 | Eval harness can fail | Supported when `--selftest` prints 19/20 and exits 0 | `python3 eval/run_cases.py --selftest` |
| C14 | Hash encoder retrieves paraphrases | Not supported | C4 |
| C15 | Chroma default ONNX embedder retrieves paraphrases in general | Not measured, except one pair in `results/negative-onnx.json` (Chinese hit, English miss). Not in `make check`. | `python3 eval/negative_retrieval.py --onnx` |
| C16 | DeepSeek answers are useful | Not measured | `tests/test_agents.py::test_agent` skips without a real key |
| C17 | Published on PyPI | False. HTTP 404 for `ai-agent-studio` on 2026-11-16. No packaging metadata. | `publish.yml` skips; no `pyproject.toml` |
| C18 | External users or a production deploy | Not claimed. No telemetry, no Dockerfile. GitHub stars/forks were 0 on 2026-11-16. | This file and the README boundaries table |
| C19 | `data/knowledge/*.md` is an accurate spec of the API | False. Demo fixture. The notes mention an envelope and sentence-transformers the gated path does not use. | Read `data/knowledge/api_design.md` against `app/api/routes.py` |

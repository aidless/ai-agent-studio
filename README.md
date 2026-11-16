# AI Agent Studio
Solves one offline check: a local FastAPI app names three roles (research, coder, writer), and a hash-trigram Chroma path loads the bundled notes and returns nearest neighbors.
Does not solve semantic search, LLM answer quality, hosted serving, or a package install. Not on PyPI, no recorded external users, and not for production.

The GitHub About text is not stored in this repository. If it still calls this a v3.0 product, that blurb is stale; this file is the claim.

[![CI](https://github.com/aidless/ai-agent-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/ai-agent-studio/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The CI badge is only the `CI` workflow. What that workflow runs, and what it skips, is in [CI coverage](#ci-coverage).

## Boundaries

| Fact | Status |
|---|---|
| PyPI project `ai-agent-studio` | HTTP 404 on 2026-11-16. No `pyproject.toml`, `setup.py`, or `setup.cfg`. No GitHub Release. `Publish to PyPI` skips the publish step. |
| External users | None recorded. No telemetry product. On 2026-11-16 the GitHub API reported `stargazers_count` 0 and `forks_count` 0. That is not a user study. |
| Production | No deploy, no SLO, no Dockerfile, no compose file. |
| Version | `0.3.0-dev` in `app/config.py`. `0.2.0-dev` on the older `agent_studio.py` script. Neither string is a release. |
| Model answers | Not measured. The LLM test is skipped unless `DEEPSEEK_API_KEY` is set, and this pass did not set a real key. |

## Offline path

Needs Python 3.12 (CI uses 3.12) and a one-time install from PyPI. After that, no API key and no model download:

```bash
pip install -r requirements-dev.txt
make check
```

On the machine recorded in `results/bench-hash.json` (CPython 3.12.3, x86_64, 4 CPUs) one `make check` took 4.59 seconds after dependencies were already installed. That is one sample, not a budget. The install needs network and is not included.

`make check` runs, in order:

1. `python3 eval/negative_retrieval.py --check` — exact copies rank first; the English paraphrase below is not semantic retrieval.
2. `python3 eval/run_cases.py` — structural checks against this tree (config, chunk sizes, route prefix, the committed hash snapshot's chunk count, the committed Chroma file's embedding count).
3. `python3 eval/run_cases.py --selftest` — corrupts one expected value and must go red. Exit 0 means it did. Exit 3 means the harness stayed green and is decorative.
4. `python3 -m pytest -q` — the assertions in `tests/`. One test is skipped without `DEEPSEEK_API_KEY`.

Refresh the committed snapshots, still offline:

```bash
python3 eval/negative_retrieval.py --write
python3 bench_rag_wiring.py
python3 eval/run_cases.py --save
```

`results/bench-hash.json` holds one timing sample (`python`, `machine`, `cpu_count`). Those seconds are not a performance spec. `results/knowledge-sha256.json` is the SHA-256 of `data/knowledge/*`. `CLAIM_LEDGER.md` maps each claim to the command that checks it.

Optional, not part of `make check` or CI: `python3 eval/negative_retrieval.py --onnx` rebuilds `results/negative-onnx.json`. The first run downloads Chroma's ONNX model (about 79MB).

## What the gate shows

Supported:

- The hash-trigram function is deterministic, 384-dimensional, and L2-normalized (`tests/test_agents.py`).
- `app/rag/document_loader.py` splits the five bundled notes into 12 chunks and a search returns 5 neighbors. Neighbors are not graded.
- `app/rag/loader.py`'s chunker, called with no database, splits the same notes into 11 chunks. That is a different function from the 12-chunk path.
- An unknown role name returns `Unknown agent: ...`. A fake agent that returns `[Agent error] ...` shows up in `pipeline.errors`, not in `final_output`.
- `GET /health` in `app/api/routes.py` says `status: up` and `llm_probed: false`.

Not supported, with a measured miss:

The hash encoder stores character trigrams only (`app/rag/vector_store.py`). On a two-note index:

- relevant note (`sem.md`): `研究员在回答之前检索知识库。`
- unrelated note (`lex.md`): `banana banana lexical marker`
- paraphrase (`PARA_EN`): `An analyst looks up notes first and then replies.`

`PARA_EN` shares no character trigram with the relevant note, so the encoder has no feature that could mean "same question." The gate requires that overlap to be 0, the exact-copy nearest neighbor to be the copied note at distance 0, and the paraphrase cosine with the relevant note to be under 0.5 (an exact copy scores 1). The committed top-1 and cosine are in `results/negative-hash.json`. A Chinese wording of the same idea, `分析员会先查资料再作答。`, also has zero trigram overlap. In that snapshot its nearest neighbor is `lex.md`, and the gap to `sem.md` is under 0.01, so that rank is not part of the gate.

The older script `agent_studio.py` does not use that encoder. Its in-memory search sums `str.count` over whitespace-separated tokens. The fragment `知识库` hits the Chinese note. `PARA_EN` does not. Its only hit is the unrelated note, with score 4, because the token `an` occurs four times inside `banana banana`. That is a false hit, not an understanding of the question.

Not measured:

- Any DeepSeek completion. `LLMFactory.create` raises `openai.OpenAIError` when `deepseek_api_key` is empty. A non-empty placeholder only gets past construction.
- Whether the server embedder (Chroma default ONNX, used by `app.rag.store` and `python -m app.main`) retrieves well. One synthetic pair is in `results/negative-onnx.json`: on chromadb 0.5.23 the Chinese paraphrase's nearest neighbor was the relevant note, and the English paraphrase's nearest neighbor was the unrelated note. n=1 pair. An unrelated query still gets a neighbor, because the index always returns one. Do not generalize.

## Two RAG implementations

| Path | Used by | Offline gate |
|---|---|---|
| `app/rag/document_loader.py` + `_hash_embedding` | `tests/test_agents.py`, `bench_rag_wiring.py`, `eval/negative_retrieval.py` | Yes. 12 chunks. Non-semantic. |
| `app/rag/loader.py` + `app/rag/store.py` | `app/main.py`, `app/api/routes.py`, the researcher and writer tools | Chunk count only (11). Search downloads Chroma's default ONNX model and is not in `make check`. |
| `agent_studio.RAGEngine` | `python agent_studio.py` only | The fragment-hit / paraphrase-miss test above. No Chroma. |

`data/chroma/chroma.sqlite3` is committed with **0 rows** in `embeddings` (eval case `CHR-01`). It is not an index of 11 or 12 chunks. The historical README curl that said `"documents": 11` matched the server chunker count, not this sqlite file.

`data/knowledge/*.md` is demo copy written for this repo. Those notes mention sentence-transformers and a `{"code": 0, ...}` response envelope. The code does not implement that envelope, and the gated embedder is the hash function, not sentence-transformers. The notes are a fixture, not a spec.

`docs/api-docs.png` is a Swagger screenshot already in the tree. This pass did not recapture it. It is not evidence of answer quality.

## Failure modes

- **Paraphrase, hash encoder.** Zero shared trigrams. Semantic retrieval is not supported. See the pair in the section above.
- **Paraphrase, keyword engine.** `agent_studio.py` hits `知识库` and, for `PARA_EN`, returns only the unrelated note (score 4 from the substring `an` inside `banana`).
- **Pipeline HTTP status.** `POST /api/v1/agent/pipeline` stays 200 when `errors` is non-empty. Callers have to read `errors`.
- **Importing the server.** `import app.main` constructs `Orchestrator`, which constructs a chat client. An empty key raises before the process serves traffic.
- **Health.** `status: up` does not mean the model or the index was checked.
- **Server search is a different code path** from the hash gate, and the committed sqlite index is empty.
- **Chroma 0.5.23** logs `Failed to send telemetry event ... capture() takes 1 positional argument` during the checks even though the client is created with `anonymized_telemetry=False`. That log is a failed client call, not proof that telemetry stayed local.
- **`_hash_embedding([123])`** raises `AttributeError`. `AgentTools.read_file(None)` raises `TypeError`. `read_file` on a missing path returns a string instead of raising.

## CI coverage

| Workflow | Runs | Does not run |
|---|---|---|
| `CI` / `verify` | `make check` on Python 3.12 | DeepSeek, ONNX download, server boot, answer quality |
| `CI` / `mutation-control` | pytest collection must fail after a syntax error is appended to a test file | The test bodies. A syntax gate, not a behavior mutation. |
| `CI` / `secret-scan` | gitleaks on full git history | Tests |
| `PR Checks` | `python -m compileall` | Dependencies and tests. Green here does not mean `make check` passed. |
| `Packaging` | Skips the build: no packaging metadata | A wheel |
| `Publish to PyPI` | Skips publish for the same reason | A release. The project is not on PyPI. |
| `SAST` | gitleaks again | Tests |

## Layout

```
agent_studio.py          # older single-file demo (keyword RAG), version 0.2.0-dev
app/main.py              # FastAPI entry. Import needs a non-empty DEEPSEEK_API_KEY.
app/agents/              # researcher, coder, writer, orchestrator
app/rag/document_loader.py + vector_store.py   # hash path used by the gate
app/rag/loader.py + store.py                   # server path, default ONNX embedder
eval/run_cases.py        # structural cases
eval/negative_retrieval.py
tests/
results/                 # committed snapshots from the commands above
```

Starting the server is outside the offline gate:

```bash
DEEPSEEK_API_KEY=placeholder python -m app.main
```

`placeholder` only gets past client construction. It was not used to call DeepSeek. Startup indexes `data/knowledge` through `app.rag.loader` and will download the ONNX model on first use. `POST /api/v1/agent/run` then calls the network. This pass did not record a model answer.

## Reproduce the negative result

`PREREG.md` is a post-hoc note. It is not a timestamped preregistration. The rule the gate enforces lives in `eval/negative_retrieval.py`.

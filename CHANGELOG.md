# Changelog

All notable changes to this repository are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Relabel the in-code version from `3.0.0` to `0.3.0-dev` (`agent_studio.py` is `0.2.0-dev`). No release was published, and the project is not on PyPI.
- `GET /health` reports `up` with `llm_probed: false`. It no longer says `healthy`.
- `Orchestrator` treats a result that starts with `[Agent error]` as an error. `pipeline` lists those steps in `errors` and does not copy them into `final_output`. HTTP status for the pipeline route is still 200.
- Offline gate is `make check`: hash-trigram negative probe, structural eval cases, eval selftest, and pytest. CI runs that gate and does not install torch or sentence-transformers.
- Governance baseline: LICENSE, security policy, code of conduct, contributor and
  support guides, issue and pull-request templates, CODEOWNERS, dependabot, and
  `.editorconfig` added. No research content changed.

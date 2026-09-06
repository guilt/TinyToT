# Changelog

All notable changes to TinyToT are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Termux/Android support** — everything installs and runs on Android/Termux
  (including under proot):
  - `pydantic-core` has no PyPI wheel for `android_30_arm64_v8a`; a
    `scripts/build-android.sh` build helper and a prebuilt wheel are provided
    (see the getting-started guide).
  - `Makefile.user.template` documents reusing an existing
    `--system-site-packages` `.venv` via `PIPENV_VENV_IN_PROJECT`, so `pipenv
    run` and all `make` targets work without pipenv rebuilding dependencies.
  - Termux `golang`'s trimmed `go` binary needs `GOROOT` + `-e` under proot; a
    detection-based wrapper (`bin/go` in the dotfiles) keeps codegen execution
    tests green without affecting other platforms.
- Android installation notes in the getting-started guide.

## [0.4.0] - 2026

### Added
- OpenTraces ingestion (`tinytot-ingest opentraces`), CS chain generator, deep
  chain scaling, camelCase API fields.
- Hot-reload of knowledge and indexes via `/api/reload`.
- Truthfulness — honest "I don't know" for unknown facts — plus a TruthfulQA
  benchmark.
- Pip-install-ready benchmarks, UTF-8 CLI output, and test cleanup.
- Reasoning parity tooling (`tinytot-parity`) and precision-first word-problem
  routing.
- Portable, filesystem-neutral API signatures in generated docs.

## [0.3.0]

### Added
- Ollama-compatible server with thinking-model support.
- Tree of Thoughts reasoning with multi-path evaluation and scoring.
- Agentic tool system: file, shell, web, search, codegen, media, translation,
  and data tools.
- Knowledge base of curated topics, code-generation templates and project
  scaffolding, offline translation engine, and multilingual support.
- Benchmark harness with parallel execution and anti-cheat.
- Packaging: pip wheel, self-replication, CLI tools, and build variants.
- Documentation: API reference, user guide, and how-to guides.
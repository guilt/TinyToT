# Changelog

All notable changes to TinyToT are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.5.0] - 2026

### Added
- **Termux/Android support** — everything installs and runs on Android/Termux,
  including under proot:
  - Rust dependencies without an `android_30_arm64_v8a` PyPI wheel
    (`pydantic-core`, `rpds-py`) build from source via the cargo-installed
    `maturin`; `scripts/build-android.sh` and prebuilt wheels are provided, and
    pip's build-isolation (which tries to rebuild `maturin`) is bypassed.
  - `Pillow` is installed from the Termux package repository: the PyPI source
    build links glibc's `libc.so.6`, which bionic cannot load.
  - Termux `golang`'s trimmed `go` binary needs `GOROOT` + `-e` under proot; a
    detection-based wrapper (`bin/go` in the dotfiles) keeps codegen execution
    tests green without affecting other platforms.
  - `Makefile.user.template` documents reusing an existing
    `--system-site-packages` `.venv` via `PIPENV_VENV_IN_PROJECT`, so `pipenv
    run` and all `make` targets work without pipenv rebuilding dependencies.
- New "Termux / Android" section in the getting-started guide, plus a README
  pointer, covering the venv/pipenv setup, the Android wheels, and the Pillow
  and Go toolchain notes.
- `CHANGELOG.md` and a documented release process.
- Hot-reload of knowledge and indexes via `/api/reload`.
- Truthfulness — honest "I don't know" for unknown facts — plus a TruthfulQA
  benchmark.
- Pip-install-ready benchmarks, UTF-8 CLI output, and test cleanup.
- Reasoning parity tooling (`tinytot-parity`) and precision-first word-problem
  routing.
- Portable, filesystem-neutral API signatures in generated docs.

### Changed
- Data-quality guard exempts auto-generated `*_augment_*.md` chains (opencode /
  OpenTraces reference material, excluded from the routing index) from the
  strict curated-chain rules; real traces may legitimately contain
  single-thought chains or terse conclusions.
- Test toolchain pinned to `pytest 8.4.x` in the venv — the shared system
  `pytest 9.0.2` did not load the venv-installed plugins (`pytest-asyncio`,
  `pytest-xdist`, `pytest-mock`, `pytest-cov`).
- Fixed two broken `../guides/concepts` links in the getting-started guide.

### Verified
- Full test suite green: 669 passed, 2 skipped (incl. Go codegen execution).
- All 11 agent tools exercised end-to-end (web, document, translate, data,
  file, shell, image, video, audio, media).
- `make docs` builds with zero warnings; `make precommit` passes all hooks
  (ruff, mypy, pre-commit-hooks, pytest, benchmark regression, data-quality).
- CLI tools verified: `tinytot`, `tinytot-clone`, `tinytot-check-data`,
  `tinytot-ingest`, `tinytot-parity`.

## [0.4.0] - 2026

### Added
- OpenTraces ingestion (`tinytot-ingest opentraces`), CS chain generator, deep
  chain scaling, camelCase API fields.

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
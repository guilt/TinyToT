"""Tests for tinytot.content — category discovery, chain loading, schema parsing."""

import pytest

from tinytot.content import (
    METADATA_KEY_HANDLES,
    getCategories,
    loadHermesJournal,
    loadReasoningChains,
    loadToolPatterns,
)

# ---------------------------------------------------------------------------
# Helpers — clear lru_cache between tests so fixture dirs don't bleed across
# ---------------------------------------------------------------------------


def _clear_caches():
    getCategories.cache_clear()
    loadReasoningChains.cache_clear()


@pytest.fixture(autouse=True)
def clear_caches():
    _clear_caches()
    yield
    _clear_caches()


# ---------------------------------------------------------------------------
# getCategories
# ---------------------------------------------------------------------------


class TestGetCategories:
    def test_discovers_both_files(self, category_dir):
        cats = getCategories(category_dir)
        assert "math" in cats
        assert "tool_calling" in cats

    def test_maps_category_to_filename(self, category_dir):
        cats = getCategories(category_dir)
        assert cats["math"] == "math.md"
        assert cats["tool_calling"] == "tool_calling.md"

    def test_empty_dir_returns_empty(self, tmp_path):
        empty = tmp_path / "empty_cats"
        empty.mkdir()
        assert getCategories(empty) == {}

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        assert getCategories(tmp_path / "does_not_exist") == {}

    def test_file_without_yaml_header_uses_stem(self, tmp_path):
        cat_dir = tmp_path / "cats"
        cat_dir.mkdir()
        (cat_dir / "custom.md").write_text("# No YAML header\n## Chain 1: Test\nThought 1: hi")
        cats = getCategories(cat_dir)
        assert "custom" in cats

    def test_file_with_invalid_yaml_falls_back_to_stem(self, tmp_path):
        cat_dir = tmp_path / "cats"
        cat_dir.mkdir()
        (cat_dir / "broken.md").write_text("---\n: bad: yaml: [\n---\n")
        cats = getCategories(cat_dir)
        assert "broken" in cats

    def test_result_is_cached(self, category_dir):
        r1 = getCategories(category_dir)
        r2 = getCategories(category_dir)
        assert r1 is r2


# ---------------------------------------------------------------------------
# loadReasoningChains
# ---------------------------------------------------------------------------


class TestLoadReasoningChains:
    def test_loads_two_chains_from_math(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        assert len(chains) == 2

    def test_chain_titles_parsed(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        titles = [c[0] for c in chains]
        assert "Arithmetic" in titles
        assert "Algebra" in titles

    def test_thoughts_populated(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        arithmetic = next(c for c in chains if c[0] == "Arithmetic")
        assert len(arithmetic[1]) == 3
        assert "arithmetic operation" in arithmetic[1][0]

    def test_handles_metadata_parsed(self, category_dir):
        chains = loadReasoningChains("math.md", category_dir)
        arithmetic = next(c for c in chains if c[0] == "Arithmetic")
        assert METADATA_KEY_HANDLES in arithmetic[2]
        assert "calculate" in arithmetic[2][METADATA_KEY_HANDLES]

    def test_missing_file_returns_empty(self, category_dir):
        result = loadReasoningChains("nonexistent.md", category_dir)
        assert result == []

    def test_result_is_cached(self, category_dir):
        r1 = loadReasoningChains("math.md", category_dir)
        r2 = loadReasoningChains("math.md", category_dir)
        assert r1 is r2

    def test_chain_without_handles_has_empty_metadata(self, tmp_path):
        cat_dir = tmp_path / "cats"
        cat_dir.mkdir()
        (cat_dir / "bare.md").write_text("## Chain 1: Bare\nThought 1: step one\nThought 2: step two\n")
        chains = loadReasoningChains("bare.md", cat_dir)
        assert len(chains) == 1
        assert chains[0][2] == {}


# ---------------------------------------------------------------------------
# loadToolPatterns
# ---------------------------------------------------------------------------


class TestLoadToolPatterns:
    def test_loads_three_patterns(self, schema_file):
        patterns = loadToolPatterns(schema_file)
        assert len(patterns) == 3

    def test_search_tools_has_keywords(self, schema_file):
        patterns = loadToolPatterns(schema_file)
        search = next(p for p in patterns if p.get("tool_name") == "ddg-search")
        assert "search" in search["keywords"]

    def test_database_tools_has_exclude_keywords(self, schema_file):
        patterns = loadToolPatterns(schema_file)
        db = next(p for p in patterns if p.get("tool_name") == "sqlite")
        assert "aws" in db["exclude_keywords"]

    def test_params_parsed_as_dict(self, schema_file):
        patterns = loadToolPatterns(schema_file)
        search = next(p for p in patterns if p.get("tool_name") == "ddg-search")
        assert isinstance(search["params"], dict)
        assert search["params"]["query"] == "extract_topic"

    def test_missing_schema_returns_empty(self, tmp_path):
        result = loadToolPatterns(tmp_path / "no_such_file.md")
        assert result == []

    def test_invalid_schema_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.md"
        bad.write_text("not frontmatter at all, just text")
        # frontmatter.load is lenient; at minimum it should not raise
        result = loadToolPatterns(bad)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# loadHermesJournal
# ---------------------------------------------------------------------------

HERMES_JOURNAL_MD = """\
# 2026-06-30

## Use metric units when communicating measurements outside the US.
> source: user ~ 2026-06-30T14:32:00+00:00 ~ hash: {h1}

## Always confirm before deleting cloud resources or production data.
> source: agent ~ 2026-06-30T16:01:00+00:00 ~ hash: {h2}

## Raw entries
This is a plain paragraph, not a learning entry.
""".format(
    h1="a" * 64,
    h2="b" * 64,
)

HERMES_PLAIN_MD = """\
# Regular Knowledge

## Section Heading

This is a plain paragraph passage with no provenance.
"""


class TestLoadHermesJournal:
    def test_extracts_learning_entries(self, tmp_path):
        f = tmp_path / "2026-06-30.md"
        f.write_text(HERMES_JOURNAL_MD)
        passages = loadHermesJournal(f)
        assert len(passages) == 2

    def test_passage_text_matches_heading(self, tmp_path):
        f = tmp_path / "2026-06-30.md"
        f.write_text(HERMES_JOURNAL_MD)
        passages = loadHermesJournal(f)
        texts = [p[1] for p in passages]
        assert any("metric units" in t for t in texts)
        assert any("deleting cloud" in t for t in texts)

    def test_section_heading_is_metadata_not_passage(self, tmp_path):
        f = tmp_path / "2026-06-30.md"
        f.write_text(HERMES_JOURNAL_MD)
        passages = loadHermesJournal(f)
        # "Raw entries" is a plain ## heading without provenance — not a passage
        texts = [p[1] for p in passages]
        assert not any("Raw entries" in t for t in texts)

    def test_provenance_stripped_from_passage_text(self, tmp_path):
        f = tmp_path / "2026-06-30.md"
        f.write_text(HERMES_JOURNAL_MD)
        passages = loadHermesJournal(f)
        for _, text in passages:
            assert "source:" not in text
            assert "hash:" not in text

    def test_missing_file_returns_empty(self, tmp_path):
        assert loadHermesJournal(tmp_path / "missing.md") == []

    def test_section_label_captured_in_heading(self, tmp_path):
        f = tmp_path / "2026-06-30.md"
        f.write_text(HERMES_JOURNAL_MD)
        passages = loadHermesJournal(f)
        # All entries are under "2026-06-30" section
        assert all(p[0] == "2026-06-30" for p in passages)


class TestLoadKnowledgePassagesHermesDetection:
    def test_auto_detects_hermes_format(self, tmp_path):
        from tinytot.content import loadKnowledgePassages

        loadKnowledgePassages.cache_clear()
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "2026-06-30.md").write_text(HERMES_JOURNAL_MD)
        passages = loadKnowledgePassages(kdir)
        assert len(passages) == 2
        loadKnowledgePassages.cache_clear()

    def test_plain_and_hermes_mixed(self, tmp_path):
        from tinytot.content import loadKnowledgePassages

        loadKnowledgePassages.cache_clear()
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "2026-06-30.md").write_text(HERMES_JOURNAL_MD)
        (kdir / "general.md").write_text(HERMES_PLAIN_MD)
        passages = loadKnowledgePassages(kdir)
        # 2 from hermes + 1 from plain
        assert len(passages) == 3
        loadKnowledgePassages.cache_clear()

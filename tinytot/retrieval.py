"""
tinytot.retrieval — Multi-headed TF-IDF retrieval, chain ranking, categorization.

Five retrieval heads (analogous to multi-head attention):
  H1  TF-IDF unigrams over title+thoughts         — standard token co-occurrence
  H2  TF-IDF over conclusion text only            — output-space representation
  H3  Character trigram overlap                   — sub-word, typo-robust
  H4  BM25 scoring (TF saturation + length norm)  — non-linear frequency weighting
  H5  Keyword frontmatter exact match             — discrete categorical signal

Each head votes independently; a weighted sum aggregates to a final score.
Head weights are tunable constants (no backprop needed).

Depends only on tinytot.content. No I/O after index build.
"""

from __future__ import annotations

import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .content import (
    CATEGORY_DIR,
    COMPILED_WORD_SHORT,
    KNOWLEDGE_DIR,
    Chain,
    getCategories,
    loadKnowledgePassages,
    loadReasoningChains,
)

logger = logging.getLogger(__name__)

__all__ = [
    "buildChainIndex",
    "buildChainMeta",
    "buildKnowledgeIndex",
    "queryVector",
    "cosineSim",
    "chainVector",
    "categorizePrompt",
    "scoreChain",
    "rankChains",
    "findKnowledgeAnswer",
    "scoreResponse",
    "multiHeadScore",
    "multiHeadScorePassage",
]

DEFAULT_CATEGORY = "tool_calling"

# ---------------------------------------------------------------------------
# Retrieval thresholds -- all cosine-similarity cutoffs live here.
# Cosine similarity ranges 0.0 (no overlap) to 1.0 (identical vocabulary).
# ---------------------------------------------------------------------------

# Minimum cosine similarity between a query and a TF-IDF chain-category vector
# for that category to be considered a valid routing candidate.  Below this,
# the query is too dissimilar to any known category and falls back to DEFAULT_CATEGORY.
TFIDF_BACKOFF_THRESHOLD: float = 0.05

# Minimum cosine similarity between a query and a knowledge passage for the
# passage to be used as grounding context in a Tree-of-Thoughts chain.
# Below this the passage is too weak to trust and the chain runs ungrounded.
KNOWLEDGE_THRESHOLD: float = 0.20

# Above this similarity the passage is returned *directly* as the answer,
# skipping the ToT reasoning chain entirely.  The passage is specific enough
# that elaboration would add noise rather than clarity.
# Raised from 0.50 → 0.65: the GSM8K corpus is large and noisy enough that
# short social/conversational prompts were scoring 0.28-0.50 against random
# passages ("Hello" matched "greet('Linda')" at 0.29).  A score of 0.65+
# indicates the passage genuinely answers the query.
KNOWLEDGE_DIRECT_THRESHOLD: float = 0.65

# Secondary threshold used for direct-mode lookups (factual questions, yes/no).
# Sits between KNOWLEDGE_THRESHOLD and KNOWLEDGE_DIRECT_THRESHOLD: strong enough
# to trust as a direct answer, but below the bar for high-confidence verbatim return.
# Lowered from 0.28 to 0.25 to accommodate short queries (e.g. "What is a 401k?")
# whose weighted scores sit in the 0.25-0.28 range after source quality weighting.
KNOWLEDGE_DIRECT_LOWER: float = 0.25

# Tool-call fallback score: returned when a tool is matched but no knowledge
# passage is available to score against.
SCORE_TOOL_RESPONSE: float = 0.3

# ---------------------------------------------------------------------------
# TF-IDF index (chains)
# ---------------------------------------------------------------------------

IndexEntry = Tuple[str, str, str]  # (category, filename, title)

MAX_CHAINS_PER_CATEGORY = 15  # cap per category so large corpora don't dominate routing

# Weight applied to keyword text when building chain index vectors.
# Prepending keywords N times effectively scales their TF contribution.
# 3 repetitions means a keyword hit adds ~3x the weight of a chain body match.
_KEYWORD_REPEAT = 3


def _loadCategoryKeywords(filename: str, categoryDir: Path) -> str:
    """Return the keywords string from a category file's YAML frontmatter.

    Returns empty string if not present.
    """
    import yaml as _yaml

    fp = categoryDir / filename
    if not fp.exists():
        return ""
    try:
        content = fp.read_text(encoding="utf-8")
    except (IOError, OSError):
        return ""
    if not content.startswith("---"):
        return ""
    end = content.find("---", 3)
    if end == -1:
        return ""
    try:
        meta = _yaml.safe_load(content[3:end].strip())
    except Exception:
        return ""
    if not meta or "keywords" not in meta:
        return ""
    kw = meta["keywords"]
    if isinstance(kw, list):
        return " ".join(kw)
    return str(kw)


@lru_cache(maxsize=1)
def buildChainIndex(
    categoryDir: Path = CATEGORY_DIR,
) -> Tuple[List[IndexEntry], Dict[str, float], List[Dict[str, float]]]:
    """Build a TF-IDF index over every chain in every category file.

    Caps each category at MAX_CHAINS_PER_CATEGORY chains so that large
    ingested corpora do not dilute IDF scores and pull routing away from
    smaller but more precise categories.

    Category keywords (from YAML frontmatter) are prepended to every chain
    in that category, repeated _KEYWORD_REPEAT times so that query tokens
    matching a category keyword provide a meaningful routing boost.
    """
    categories = getCategories(categoryDir)
    entries: List[IndexEntry] = []
    raw_texts: List[str] = []

    for category, filename in categories.items():
        chains = loadReasoningChains(filename, categoryDir)
        keywords = _loadCategoryKeywords(filename, categoryDir)
        # Repeat keywords to amplify their TF weight in the chain vectors
        keywordPrefix = (keywords + " ") * _KEYWORD_REPEAT if keywords else ""
        for title, thoughts, _ in chains[:MAX_CHAINS_PER_CATEGORY]:
            text = (keywordPrefix + title + " " + " ".join(thoughts)).lower()
            entries.append((category, filename, title))
            raw_texts.append(text)

    return _buildIndex(entries, raw_texts)


# Metadata bundle for multi-head chain scoring (parallel cache to buildChainIndex)
ChainMeta = Tuple[str, List[str], str, str]  # (title, thoughts, conclusion, keywords)


@lru_cache(maxsize=1)
def buildChainMeta(
    categoryDir: Path = CATEGORY_DIR,
) -> Tuple[List[IndexEntry], List[ChainMeta], float]:
    """Return chain metadata and average document length for multi-head scoring.

    Returns:
        entries       — (category, filename, title) list, same order as buildChainIndex
        chain_metas   — (title, thoughts, conclusion, keywords) per chain
        avg_doc_len   — average token count across all chain documents
    """
    categories = getCategories(categoryDir)
    entries: List[IndexEntry] = []
    metas: List[ChainMeta] = []
    total_tokens = 0

    for category, filename in categories.items():
        chains = loadReasoningChains(filename, categoryDir)
        keywords = _loadCategoryKeywords(filename, categoryDir)
        for title, thoughts, meta_dict in chains[:MAX_CHAINS_PER_CATEGORY]:
            conclusion = meta_dict.get("conclusion", "")
            entries.append((category, filename, title))
            metas.append((title, thoughts, conclusion, keywords))
            doc_tokens = COMPILED_WORD_SHORT.findall((title + " " + " ".join(thoughts)).lower())
            total_tokens += len(doc_tokens)

    avg_len = total_tokens / len(entries) if entries else 10.0
    return entries, metas, avg_len


# ---------------------------------------------------------------------------
# TF-IDF index (knowledge)
# ---------------------------------------------------------------------------

KnowledgeEntry = Tuple[str, str]  # (heading, passage_text)


@lru_cache(maxsize=1)
def buildKnowledgeIndex(
    knowledgeDir: Path = KNOWLEDGE_DIR,
) -> Tuple[List[KnowledgeEntry], Dict[str, float], List[Dict[str, float]]]:
    """Build a TF-IDF index over every passage in every knowledge file."""
    passages = loadKnowledgePassages(knowledgeDir)
    raw_texts = [(heading + " " + text).lower() for heading, text in passages]
    return _buildIndex(passages, raw_texts)


@lru_cache(maxsize=1)
def _knowledgeAvgDocLen(knowledgeDir: Path = KNOWLEDGE_DIR) -> float:
    """Average passage body token count — used by BM25 head (H4)."""
    passages = loadKnowledgePassages(knowledgeDir)
    if not passages:
        return 50.0
    total = sum(len(COMPILED_WORD_SHORT.findall(text.lower())) for _, text in passages)
    return total / len(passages)


# ---------------------------------------------------------------------------
# Shared index builder
# ---------------------------------------------------------------------------


def _buildIndex(
    entries: List,
    raw_texts: List[str],
) -> Tuple[List, Dict[str, float], List[Dict[str, float]]]:
    N = len(raw_texts)
    if N == 0:
        return [], {}, []

    df: Dict[str, int] = {}
    tfRaw: List[Dict[str, int]] = []
    for text in raw_texts:
        tokens = set(COMPILED_WORD_SHORT.findall(text))
        tfRaw.append({t: text.count(t) for t in tokens})
        for t in tokens:
            df[t] = df.get(t, 0) + 1

    idf: Dict[str, float] = {t: math.log((N + 1) / (count + 1)) + 1.0 for t, count in df.items()}

    tfVecs: List[Dict[str, float]] = []
    for raw in tfRaw:
        total = sum(raw.values()) or 1
        vec = {t: (count / total) * idf.get(t, 1.0) for t, count in raw.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        tfVecs.append({t: v / norm for t, v in vec.items()})

    return entries, idf, tfVecs


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------


def queryVector(prompt: str, idf: Dict[str, float]) -> Dict[str, float]:
    """Build a unit-norm TF-IDF vector for a query string."""
    tokens = COMPILED_WORD_SHORT.findall(prompt.lower())
    if not tokens:
        return {}
    tf: Dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1.0
    total = len(tokens)
    vec = {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def cosineSim(qvec: Dict[str, float], dvec: Dict[str, float]) -> float:
    """Dot product of two pre-normalized unit vectors."""
    return sum(qvec[t] * dvec[t] for t in qvec if t in dvec)


def chainVector(title: str, thoughts: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """Build a unit-norm TF-IDF vector for a single chain (title + thoughts)."""
    text = (title + " " + " ".join(thoughts)).lower()
    tokens = COMPILED_WORD_SHORT.findall(text)
    if not tokens:
        return {}
    tf: Dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1.0
    total = len(tokens)
    vec = {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


# ---------------------------------------------------------------------------
# Multi-headed retrieval (5 heads)
# ---------------------------------------------------------------------------

# Head weights: sum to ~1.0.  Tuned so that H1 (unigram TF-IDF) + H4 (BM25)
# carry most signal, while H3 (trigram) and H5 (keyword) provide complementary
# signal for short queries and exact category signals respectively.
_HEAD_WEIGHTS = {
    "h1_tfidf": 0.35,  # standard unigram TF-IDF cosine
    "h2_conclusion": 0.15,  # TF-IDF over conclusion text only
    "h3_trigram": 0.10,  # character trigram overlap
    "h4_bm25": 0.30,  # BM25 (TF saturation + IDF)
    "h5_keyword": 0.10,  # keyword frontmatter exact token hit
}

# BM25 free parameters
_BM25_K1: float = 1.5  # TF saturation: higher = less saturation
_BM25_B: float = 0.75  # length normalisation: 0 = none, 1 = full


def _trigrams(text: str) -> Dict[str, int]:
    """Return character trigram frequency dict for a string."""
    t = re.sub(r"\s+", " ", text.lower().strip())
    result: Dict[str, int] = {}
    for i in range(len(t) - 2):
        tri = t[i : i + 3]
        result[tri] = result.get(tri, 0) + 1
    return result


def _trigram_sim(a: str, b: str) -> float:
    """Cosine similarity between character trigram vectors."""
    va = _trigrams(a)
    vb = _trigrams(b)
    if not va or not vb:
        return 0.0
    dot = sum(va.get(k, 0) * vb.get(k, 0) for k in va if k in vb)
    norm_a = math.sqrt(sum(v * v for v in va.values()))
    norm_b = math.sqrt(sum(v * v for v in vb.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    idf: Dict[str, float],
    avg_doc_len: float,
) -> float:
    """BM25 score for a query against a document."""
    dl = len(doc_tokens)
    if dl == 0 or avg_doc_len == 0:
        return 0.0
    tf_doc: Dict[str, int] = {}
    for t in doc_tokens:
        tf_doc[t] = tf_doc.get(t, 0) + 1
    score = 0.0
    for t in query_tokens:
        if t not in tf_doc:
            continue
        tf = tf_doc[t]
        idf_val = idf.get(t, 1.0)
        numerator = tf * (_BM25_K1 + 1)
        denominator = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avg_doc_len)
        score += idf_val * (numerator / denominator)
    return score


def _keyword_hit(query: str, keywords: str) -> float:
    """Fraction of query 3+-char tokens that appear in the keywords string."""
    q_tokens = set(COMPILED_WORD_SHORT.findall(query.lower()))
    kwTokens = set(COMPILED_WORD_SHORT.findall(keywords.lower()))
    if not q_tokens or not kwTokens:
        return 0.0
    hits = q_tokens & kwTokens
    return len(hits) / len(q_tokens)


def multiHeadScore(
    query: str,
    chain_title: str,
    chain_thoughts: List[str],
    chain_conclusion: str,
    chain_keywords: str,
    idf: Dict[str, float],
    avg_doc_len: float,
) -> float:
    """Compute a weighted multi-head similarity score between query and a chain.

    Aggregates five independent scoring heads:
      H1  TF-IDF cosine on title+thoughts
      H2  TF-IDF cosine on conclusion text
      H3  Character trigram cosine
      H4  BM25 on title+thoughts tokens
      H5  Keyword frontmatter exact token hit rate
    """
    q_tokens = COMPILED_WORD_SHORT.findall(query.lower())
    if not q_tokens:
        return 0.0

    # --- H1: TF-IDF cosine on title+thoughts ---
    qvec = queryVector(query, idf)
    dvec = chainVector(chain_title, chain_thoughts, idf)
    h1 = cosineSim(qvec, dvec)

    # --- H2: TF-IDF cosine on conclusion only ---
    if chain_conclusion:
        concTokens = COMPILED_WORD_SHORT.findall(chain_conclusion.lower())
        concTf: Dict[str, float] = {}
        for t in concTokens:
            concTf[t] = concTf.get(t, 0) + 1.0
        total = len(concTokens) or 1
        conc_vec = {t: (cnt / total) * idf.get(t, 1.0) for t, cnt in concTf.items()}
        norm = math.sqrt(sum(v * v for v in conc_vec.values())) or 1.0
        conc_vec = {t: v / norm for t, v in conc_vec.items()}
        h2 = cosineSim(qvec, conc_vec)
    else:
        h2 = 0.0

    # --- H3: Character trigram similarity (query vs title+conclusion) ---
    doc_text = chain_title + " " + " ".join(chain_thoughts[:2]) + " " + chain_conclusion
    h3 = _trigram_sim(query, doc_text)

    # --- H4: BM25 on title+thoughts tokens ---
    doc_tokens = COMPILED_WORD_SHORT.findall((chain_title + " " + " ".join(chain_thoughts)).lower())
    raw_bm25 = _bm25_score(q_tokens, doc_tokens, idf, avg_doc_len)
    # Normalise BM25 to [0,1] with a soft cap at 5.0
    h4 = min(raw_bm25 / 5.0, 1.0)

    # --- H5: Keyword exact hit fraction ---
    h5 = _keyword_hit(query, chain_keywords) if chain_keywords else 0.0

    w = _HEAD_WEIGHTS
    return (
        w["h1_tfidf"] * h1 + w["h2_conclusion"] * h2 + w["h3_trigram"] * h3 + w["h4_bm25"] * h4 + w["h5_keyword"] * h5
    )


def multiHeadScorePassage(
    query: str,
    heading: str,
    passage: str,
    idf: Dict[str, float],
    avg_doc_len: float,
    source_weight: float = 1.0,
) -> float:
    """Multi-head similarity score for a knowledge passage.

    Same five heads as chain scoring, adapted for passage retrieval:
      H1  TF-IDF cosine on heading+passage
      H2  TF-IDF cosine on passage only (no heading)
      H3  Character trigram cosine
      H4  BM25 on passage tokens
      H5  Heading token overlap with query (exact match signal)
    """
    q_tokens = COMPILED_WORD_SHORT.findall(query.lower())
    if not q_tokens:
        return 0.0

    qvec = queryVector(query, idf)

    # --- H1: TF-IDF cosine on heading + passage ---
    fullText = (heading + " " + passage).lower()
    fullTokens = COMPILED_WORD_SHORT.findall(fullText)
    fullTf: Dict[str, float] = {}
    for t in fullTokens:
        fullTf[t] = fullTf.get(t, 0) + 1.0
    total = len(fullTokens) or 1
    full_vec = {t: (cnt / total) * idf.get(t, 1.0) for t, cnt in fullTf.items()}
    norm = math.sqrt(sum(v * v for v in full_vec.values())) or 1.0
    full_vec = {t: v / norm for t, v in full_vec.items()}
    h1 = cosineSim(qvec, full_vec)

    # --- H2: TF-IDF cosine on passage body only ---
    bodyTokens = COMPILED_WORD_SHORT.findall(passage.lower())
    bodyTf: Dict[str, float] = {}
    for t in bodyTokens:
        bodyTf[t] = bodyTf.get(t, 0) + 1.0
    btotal = len(bodyTokens) or 1
    body_vec = {t: (cnt / btotal) * idf.get(t, 1.0) for t, cnt in bodyTf.items()}
    bnorm = math.sqrt(sum(v * v for v in body_vec.values())) or 1.0
    body_vec = {t: v / bnorm for t, v in body_vec.items()}
    h2 = cosineSim(qvec, body_vec)

    # --- H3: Character trigram (query vs heading+first 200 chars of passage) ---
    h3 = _trigram_sim(query, heading + " " + passage[:200])

    # --- H4: BM25 on passage body ---
    raw_bm25 = _bm25_score(q_tokens, bodyTokens, idf, avg_doc_len)
    h4 = min(raw_bm25 / 5.0, 1.0)

    # --- H5: Heading exact token overlap ---
    h5 = _keyword_hit(query, heading)

    w = _HEAD_WEIGHTS
    raw = w["h1_tfidf"] * h1 + w["h2_conclusion"] * h2 + w["h3_trigram"] * h3 + w["h4_bm25"] * h4 + w["h5_keyword"] * h5
    return raw * source_weight


# ---------------------------------------------------------------------------
# Knowledge answer lookup
# ---------------------------------------------------------------------------


# Headings from large noisy corpora that should be penalised in direct factual
# retrieval.  These datasets (epistemic reasoning, dialogue, social inference)
# produce high cosine similarity on incidental vocabulary overlaps rather than
# genuine topical relevance.
_NOISY_HEADING_RE = re.compile(
    r"\b(?:epistemic|temporal|social|commonsense|dialogue|reasoning\s+about"
    r"|inference|entailment|hypothesis|premise|situation|context|question"
    r"|mask|fill.in|reading\s+comprehension|physical\s+intuition"
    r"|unscrambl\w*|scrambl\w*|word.sort\w*|word.order|anagram|rearrang"
    r"|humaneval|code.line.desc|hyperbaton|navigate|object.count"
    r"|logical.fallacy|misconception|sports.understand|vitaminc"
    r"|checkmate|chess|colored.object|wino|timedial|strategyqa"
    r"|analogical|analytic.entailment|causal.judgment"
    r"|alphabetical|physics\s+knowledge|physics\s+problems|physics\s+questions"
    r"|math\s+problems|facts\s+vs\s+myths|sport\s+facts|sport\s+knowledge"
    r"|activity\s+reason|causal\s+reason|commonsense\s+reason|visual\s+reason"
    r"|winograd|object\s+color|temporal\s+dialogue|temporal\s+sequence"
    r"|direction\s+problem|counting\s+problem"
    r"|fact\s+verif\w*|factual\s+verif\w*|knowledge\s+conflict\w*|contextual\s+knowledge"
    r"|hellaswag\w*|social.iqa|social\s+iqa|strateg\w*"
    r"|sports\s+facts|sports\s+knowledge|sports\s+understand\w*)\b",
    re.IGNORECASE,
)

# Multiplier applied to passages whose heading matches _NOISY_HEADING_RE.
# 0.6 means a noisy passage needs a raw score 67% higher than a clean passage
# to beat it.  Raise toward 1.0 if legitimate answers come from noisy sources.
NOISY_SOURCE_PENALTY: float = 0.6


def _sourceWeight(heading: str, passage: str) -> float:
    """Return a quality multiplier for a knowledge passage based on its source."""
    if _NOISY_HEADING_RE.search(heading):
        return NOISY_SOURCE_PENALTY
    # Passages with fill-in-the-blank markers are templated Q&A, not encyclopaedic
    if "<MASK>" in passage or "<mask>" in passage:
        return NOISY_SOURCE_PENALTY
    # Creative writing "Situation:" passages describe scenes, not factual answers
    if passage.startswith("Situation:"):
        return NOISY_SOURCE_PENALTY
    if passage.startswith("Q:") and "Answer:" in passage:
        return 1.3
    if passage.startswith("Q:") and " A:" in passage[:80]:
        return 1.15
    return 1.0


def findKnowledgeAnswer(
    prompt: str,
    knowledgeDir: Path = KNOWLEDGE_DIR,
) -> Optional[Tuple[str, float]]:
    """Return (passage, score) if a knowledge passage scores above KNOWLEDGE_THRESHOLD.

    Two-stage retrieval:
      Stage 1 (coarse): TF-IDF cosine over all passages — fast O(N) scan to
                        select the top-K candidates.
      Stage 2 (rerank): Multi-head scoring on the top-K candidates — applies
                        BM25, trigram, conclusion, and keyword heads for precision.

    This mirrors how production retrieval systems work: ANN index for recall,
    cross-encoder re-ranker for precision.
    """
    _TOP_K = 20  # number of TF-IDF candidates to re-rank with multi-head

    entries, idf, tfVecs = buildKnowledgeIndex(knowledgeDir)
    if not entries:
        return None

    qvec = queryVector(prompt, idf)
    if not qvec:
        return None

    # Stage 1: fast TF-IDF coarse retrieval with source quality weighting
    weighted_scores = [
        cosineSim(qvec, dv) * _sourceWeight(heading, text) for (heading, text), dv in zip(entries, tfVecs)
    ]

    # Get top-K indices by TF-IDF score
    top_k_idx = sorted(range(len(weighted_scores)), key=lambda i: weighted_scores[i], reverse=True)[:_TOP_K]

    # Quick check: if best TF-IDF score is too low, skip multi-head entirely
    if weighted_scores[top_k_idx[0]] < KNOWLEDGE_THRESHOLD:
        return None

    # Stage 2: multi-head re-ranking of top-K candidates
    avg_len = _knowledgeAvgDocLen(knowledgeDir)
    reranked: List[Tuple[float, int]] = []
    for idx in top_k_idx:
        heading, text = entries[idx]
        sw = _sourceWeight(heading, text)
        # Cap source weight at 1.0 in multi-head context: the Q&A boost (+15%)
        # was calibrated for single-head cosine and over-promotes Q&A passages
        # when combined with BM25's frequency-boosting.
        sw = min(sw, 1.0)
        mh = multiHeadScorePassage(prompt, heading, text, idf, avg_len, source_weight=sw)
        reranked.append((mh, idx))

    reranked.sort(reverse=True)
    bestMhScore, best_idx = reranked[0]

    # Use the original TF-IDF score for threshold comparison (multi-head magnitude differs)
    bestTfidfScore = weighted_scores[best_idx]
    if bestTfidfScore < KNOWLEDGE_THRESHOLD:
        return None

    _, passage_text = entries[best_idx]
    return passage_text, bestTfidfScore


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


def categorizePrompt(prompt: str, categoryDir: Path = CATEGORY_DIR) -> str:
    """Return best-matching category name via TF-IDF cosine similarity.

    Uses the proven single-head TF-IDF approach for routing — multi-head
    scoring is applied to knowledge passage retrieval (findKnowledgeAnswer)
    where it improves precision, but routing accuracy is already 100% with
    single-head TF-IDF + keyword repeat boosting and multi-head adds noise.
    """
    entries, idf, tfVecs = buildChainIndex(categoryDir)
    if not entries:
        return DEFAULT_CATEGORY

    qvec = queryVector(prompt, idf)
    if not qvec:
        return DEFAULT_CATEGORY

    scores = [cosineSim(qvec, dv) for dv in tfVecs]
    best = max(scores)

    if best < TFIDF_BACKOFF_THRESHOLD:
        # Fallback: keyword + title token overlap
        _, chain_metas, _ = buildChainMeta(categoryDir)
        title_scores: List[Tuple[float, str]] = []
        for (category, _, title), (_, _, _, keywords) in zip(entries, chain_metas):
            titleTokens = set(COMPILED_WORD_SHORT.findall(title.lower()))
            kwTokens = set(COMPILED_WORD_SHORT.findall(keywords.lower()))
            all_tokens = titleTokens | kwTokens
            sim = sum(qvec.get(t, 0.0) for t in all_tokens)
            title_scores.append((sim, category))
        title_scores.sort(key=lambda x: -x[0])
        return title_scores[0][1] if title_scores[0][0] > 0 else DEFAULT_CATEGORY

    return entries[scores.index(best)][0]


# ---------------------------------------------------------------------------
# Chain scoring & ranking
# ---------------------------------------------------------------------------

# SCORE_TOOL_RESPONSE is defined with the other retrieval thresholds above.
SCORE_MAX = 1.0
MAX_EVALUATED_PATHS = 3


def scoreChain(
    prompt: str,
    chain: Chain,
    idf: Dict[str, float],
    has_tool_result: bool = False,
) -> float:
    """Return cosine similarity score for a chain against prompt."""
    title, thoughts, _ = chain
    dvec = chainVector(title, thoughts, idf)
    qvec = queryVector(prompt, idf)
    score = cosineSim(qvec, dvec) if qvec else 0.0
    if has_tool_result:
        score = min(score + SCORE_TOOL_RESPONSE, SCORE_MAX)
    return score


def rankChains(
    prompt: str,
    chains: List[Chain],
    idf: Dict[str, float],
) -> List[Tuple[Chain, float]]:
    """Return chains sorted by descending score, capped at MAX_EVALUATED_PATHS.

    Greedy fast-path: if exactly one chain scores non-zero, skip full sort.
    """
    scored = [(chain, scoreChain(prompt, chain, idf)) for chain in chains]

    non_zero = [(c, s) for c, s in scored if s > 0]
    if len(non_zero) == 1:
        return non_zero

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:MAX_EVALUATED_PATHS]


def scoreResponse(
    response_text: str,
    knowledgeDir: Path = KNOWLEDGE_DIR,
) -> float:
    """Score a text against the knowledge base, returning a float in [0.0, 1.0].

    Normalises the raw cosine similarity so that:
    - A response at or above KNOWLEDGE_DIRECT_THRESHOLD scores near 1.0
    - A response at KNOWLEDGE_THRESHOLD scores around 0.5
    - A response below KNOWLEDGE_THRESHOLD scores 0.0

    This gives the LLM judge scorers a meaningful gradient rather than raw
    similarity values that would always be well below 1.0 for realistic text.
    """
    entries, idf, tfVecs = buildKnowledgeIndex(knowledgeDir)
    if not entries or not response_text.strip():
        return 0.0

    qvec = queryVector(response_text, idf)
    if not qvec:
        return 0.0

    raw = max([cosineSim(qvec, dv) for dv in tfVecs])

    if raw < KNOWLEDGE_THRESHOLD:
        return 0.0

    # Normalise: map [KNOWLEDGE_THRESHOLD, KNOWLEDGE_DIRECT_THRESHOLD] → [0.5, 1.0]
    # and anything at or above KNOWLEDGE_DIRECT_THRESHOLD → 1.0
    normalised = 0.5 + 0.5 * (raw - KNOWLEDGE_THRESHOLD) / (KNOWLEDGE_DIRECT_THRESHOLD - KNOWLEDGE_THRESHOLD)
    return round(min(normalised, 1.0), 4)

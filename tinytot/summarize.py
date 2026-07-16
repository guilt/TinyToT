"""
tinytot.summarize -- Abstractive-style document summarisation using TF-IDF sentence election.

Algorithm (TextRank-inspired, no external NLP deps):
  1. Split document into sentences.
  2. Build TF-IDF vector for every sentence.
  3. Score each sentence by its average cosine similarity to all others
     (a sentence central to the document's vocabulary scores highest).
  4. Greedily select top-scoring sentences until the word budget is met,
     then return them in their original order so the summary reads naturally.

For large documents (novels, codebases), arc-aware summarisation is used:
  - Split into NARRATIVE_ARCS equal sections (default 4: setup/rising/climax/resolution).
  - Elect the best narrative sentence from each arc using TF-IDF + plot-verb weighting.
  - Each elected sentence is distilled by _distillClause() to strip temporal preamble and
    scene-setting openers, exposing the core SVO clause.
  - Consecutive distilled clauses are joined by _causalConnect() which picks a connector
    that implies narrative causality (e.g. "So", "but", "until") based on the event types
    of the two arcs being joined.
  - The result reads like a human-authored abstract rather than a list of lifted sentences.

Usage:
    from tinytot.summarize import summarizeDocument, summarizeFile
    text = open("lotr.txt").read()
    print(summarizeDocument(text, max_words=50))
"""

from __future__ import annotations

import math
import re
from pathlib import Path

__all__ = ["summarizeDocument", "summarizeFile"]

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

CHUNK_SENTENCES: int = 150  # sentences per chunk for large docs
INTER_WORDS: int = 80  # word budget per chunk's intermediate summary
MIN_SENTENCE_WORDS: int = 6  # ignore fragments shorter than this
MAX_SENTENCE_WORDS: int = 55  # ignore run-on sentences longer than this
NARRATIVE_ARCS: int = 4  # number of story sections to extract (setup/rising/climax/resolution)

# Minimum sentence count to trigger the arc-aware structural path.
# Below this threshold the flat TF-IDF centrality path runs instead.
# Set to 5 so even very short passages (news briefs, abstracts, eval cases)
# get arc-structured treatment.  5 sentences = minimum viable 2-arc layout.
ARC_THRESHOLD: int = 5

# ---------------------------------------------------------------------------
# Scoring weights -- every float that influences sentence ranking lives here.
# Raise a weight to make that signal dominate; lower it to soften its effect.
# ---------------------------------------------------------------------------

# Arc-position fraction at which a document transitions between narrative roles.
# 0.0 = start, 1.0 = end.  These partition the arc index into four bands.
ARC_ROLE_SETUP_END: float = 0.30  # first 30% is setup
ARC_ROLE_COMPLICATION_END: float = 0.60  # 30-60% is complication
ARC_ROLE_CRISIS_END: float = 0.85  # 60-85% is crisis; remainder is resolution

# Front/back matter skip fractions.  The first SKIP_FRONT fraction of a document
# is often prologue/foreword; the last SKIP_BACK fraction is often appendices.
# Too large = miss early plot events; too small = pick up irrelevant preamble.
SKIP_FRONT_FRACTION: float = 0.04  # global skip (index, ToC, copyright page)
SKIP_BACK_FRACTION: float = 0.02  # global skip (index, bibliography)
NARRATIVE_SKIP_FRONT: float = 0.15  # per-book narrative skip (forewords, prologues)
NARRATIVE_SKIP_BACK: float = 0.05  # per-book narrative skip (appendices, notes)

# Sentence length sweet-spot for arc election.
# Sentences shorter than SHORT_SENTENCE_WORDS are likely fragments (low signal).
# Sentences in the sweet spot carry a complete clause without excess noise.
# Sentences longer than LONG_SENTENCE_WORDS are run-ons that dilute per-word IDF.
SHORT_SENTENCE_WORDS: int = 8
SWEET_SENTENCE_WORDS: int = 18
LONG_SENTENCE_WORDS: int = 25

# Length-based score multipliers applied to sentences outside the sweet spot.
WEIGHT_SHORT_SENTENCE: float = 0.6  # fragment penalty -- raises if short sentences carry key facts
WEIGHT_SWEET_SENTENCE: float = 1.2  # sweet-spot bonus
WEIGHT_LONG_SENTENCE: float = 0.7  # run-on penalty -- lowers if long sentences are still precise

# Plot-verb score multipliers.
# A sentence with a past-tense transitive verb is more likely to describe an event.
# A stative sentence (stayed, waited, remained) describes state, not action.
# A dialogue sentence echoes speech rather than narrating plot.
WEIGHT_PLOT_VERB: float = 1.8  # event sentence bonus
WEIGHT_STATIVE_VERB: float = 0.5  # non-action state penalty
WEIGHT_DIALOGUE_SENTENCE: float = 0.15  # speech attribution penalty (used in _narrativeWeight)
WEIGHT_DIALOGUE_BLEED: float = 0.4  # sentence with embedded closing quotes (mixed dialogue)

# Entity-density multiplier in the base score formula: (1 + density * ENTITY_DENSITY_SCALE).
# At 0 density the entity term is 1.0 (neutral).  A sentence naming three distinct
# entities in ten words has density 0.3 → contribution 1 + 0.3*6 = 2.8.
# Raise this to make entity-rich sentences dominate; lower it to weight IDF more.
ENTITY_DENSITY_SCALE: float = 6.0

# Position boost range for arc-internal sentences.
# Sentence at arc start gets POS_BOOST_START; sentence at arc end gets POS_BOOST_END.
# A mild ramp (0.9-1.1) slightly favours chapter endings without overriding content signals.
POS_BOOST_START: float = 0.9
POS_BOOST_END: float = 1.1  # POS_BOOST_START + 0.2

# Greedy word-budget selection: stop adding sentences once this fraction of
# max_words is filled.  0.85 means "accept a ~15% undershoot" to avoid forcing
# an oversized sentence at the end.
BUDGET_FILL_FRACTION: float = 0.85

# Arc-stitching: allow the composed summary to exceed max_words by this fraction
# to accommodate connector words (Later, At the turning point, etc.).
STITCH_OVERSHOOT: float = 1.15

# IDF average threshold for allowing a single-entity sentence into structural
# event detection.  Sentences with avg IDF below this threshold are scene-setting
# filler; those above introduce rare, document-specific vocabulary (likely key events).
# Typical IDF average in a novel ranges 3-6; 4.5 sits at the upper-middle.
MIN_SINGLE_ENTITY_IDF: float = 4.5

# IDF sample size cap: build the global IDF from at most this many sentences
# (evenly spaced).  A full novel has ~8000 sentences; sampling 3000 captures
# the vocabulary distribution with a 3x speedup.
IDF_SAMPLE_MAX: int = 3000

# Minimum sentence frequency for an entity to be considered "important enough"
# to add to the per-document entity pattern.  Scales with document size via
# ENTITY_FREQ_PER_SENTENCE so short documents keep a low bar.
ENTITY_MIN_FREQ: int = 3
ENTITY_FREQ_PER_SENTENCE: int = 500  # effective_min = max(ENTITY_MIN_FREQ, n_sentences // this)
WORD_RE = re.compile(r"\b\w{3,}\b")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"''“”])")

# Common English stop words (kept short -- IDF handles the rest)
_STOPWORDS = frozenset(
    "the a an and or but in on at to for of with by from is was are were be"
    " been being have has had do does did will would could should may might"
    " shall not no nor so yet both either neither this that these those it"
    " its he she they we you i me him her them us my his our your their"
    " which who whom whose when where why how all any some such each every"
    " more most than then as up out if about into through over after".split()
)

# Common sentence-opener words and generic capitalized words excluded from
# named-entity extraction.  These are words that appear capitalized in normal
# English text but are not proper names.
_ENTITY_OPENERS = frozenset(
    {
        # pronouns / articles / conjunctions
        "The",
        "A",
        "An",
        "He",
        "She",
        "They",
        "It",
        "His",
        "Her",
        "Their",
        "This",
        "That",
        "These",
        "Those",
        "When",
        "After",
        "Before",
        "As",
        "Since",
        "While",
        "Though",
        "Although",
        "Because",
        "If",
        "But",
        "And",
        "So",
        "Yet",
        "For",
        "Nor",
        "Or",
        "Not",
        # months / days (always capitalised but not character names)
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        # common discourse words that happen to appear capitalised
        "However",
        "Moreover",
        "Therefore",
        "Furthermore",
        "Nevertheless",
        "Nonetheless",
        "Indeed",
        "Meanwhile",
        "Perhaps",
        "Certainly",
        "Actually",
        "Finally",
        "First",
        "Second",
        "Third",
        "Also",
        "Thus",
        "Hence",
        "Still",
        "Now",
        "Then",
        "There",
        # generic narrative terms
        "Chapter",
        "Book",
        "Part",
        "Note",
        "Tale",
        "Story",
        "History",
        "Appendix",
        "Index",
        "Table",
        "Figure",
        # common adjective/noun starters
        "Great",
        "Good",
        "New",
        "Old",
        "Long",
        "High",
        "Dark",
        "White",
        "Black",
        "Red",
        "Blue",
        "Green",
        "Small",
        "Large",
        "Last",
        "Next",
        "Own",
        # title words that should not be treated as entity names on their own
        "Lord",
        "Lady",
        "King",
        "Queen",
        "Prince",
        "Princess",
        "Master",
        "Mister",
        "Mistress",
        "Sir",
    }
)

# ---------------------------------------------------------------------------
# Sentence utilities
# ---------------------------------------------------------------------------


def _splitSentences(text: str) -> list[str]:
    """Split text into sentences, filtering fragments and run-ons."""
    text = re.sub(r"\s+", " ", text).strip()
    raw = SENTENCE_SPLIT_RE.split(text)
    sentences = []
    for s in raw:
        s = s.strip()
        wc = len(s.split())
        if MIN_SENTENCE_WORDS <= wc <= MAX_SENTENCE_WORDS:
            sentences.append(s)
    return sentences


def _tokenize(sentence: str) -> list[str]:
    return [w for w in WORD_RE.findall(sentence.lower()) if w not in _STOPWORDS]


# ---------------------------------------------------------------------------
# TF-IDF vectorisation (pure Python, no numpy)
# ---------------------------------------------------------------------------


def _buildTfIdf(sentences: list[str]) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Return (unit-norm TF-IDF vectors, idf table) for each sentence."""
    if not sentences:
        return [], {}

    token_lists = [_tokenize(s) for s in sentences]
    N = len(sentences)

    df: dict[str, int] = {}
    for tokens in token_lists:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    idf = {t: math.log((N + 1) / (count + 1)) + 1.0 for t, count in df.items()}

    vectors: list[dict[str, float]] = []
    for tokens in token_lists:
        if not tokens:
            vectors.append({})
            continue
        total = len(tokens)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        vec = {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({t: v / norm for t, v in vec.items()})

    return vectors, idf


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(a[t] * b[t] for t in a if t in b)


# ---------------------------------------------------------------------------
# Sentence scoring
# ---------------------------------------------------------------------------


def _scoreByLexicalCentrality(vectors: list[dict[str, float]]) -> list[float]:
    """Score each sentence by its average similarity to all others."""
    n = len(vectors)
    if n == 0:
        return []
    scores = []
    for i, v in enumerate(vectors):
        total = sum(_cosine(v, vectors[j]) for j in range(n) if j != i)
        scores.append(total / max(n - 1, 1))
    return scores


# ---------------------------------------------------------------------------
# Narrative vs. dialogue weighting
# ---------------------------------------------------------------------------

_DIALOGUE_RE = re.compile(
    r"""^["'`‘’“”]|"""  # starts with a quote character (including backtick)
    r"""[.!?]['”]\s+[A-Z]|"""  # ends spoken-line mid-sentence: .' Together ...
    r"""['’][^'’]{0,30}[!?]$|"""  # ends with open-quote fragment: 'King! or "Help me!
    r"""\bsaid\b.{0,20}$""",  # ends with "said X"
    re.IGNORECASE,
)

# Past-tense transitive verbs that signal a plot event or state change.
# These are domain-agnostic: each verb works equally for fiction, history,
# science, medicine, law, or business writing.
# Removed fiction-specific: crowned, forged, summoned, shattered, corrupted,
#   awakened, sacrificed, consumed, sailed (voyage context only).
# Added domain-neutral: published, released, launched, signed, appointed,
#   approved, rejected, proposed, concluded, demonstrated, established,
#   announced, completed, introduced, implemented, adopted, passed, founded.
_PLOT_VERB_RE = re.compile(
    r"\b(?:"
    # --- change-of-state verbs (universal) ---
    r"found|escaped|arrived|discovered|returned|revealed|"
    r"fell|rose|left|entered|crossed|reached|began|ended|"
    r"decided|learned|realized|failed|succeeded|died|born|became|"
    r"transformed|restored|separated|reunited|departed|received|"
    # --- conflict / action verbs (fiction + history + journalism) ---
    r"fought|killed|destroyed|fled|attacked|defeated|betrayed|"
    r"invaded|conquered|occupied|declared|erupted|collapsed|seized|"
    r"captured|rescued|surrendered|carried|brought|took|gave|sent|"
    r"led|followed|joined|marched|assembled|surrounded|inherited|"
    # --- change / achievement verbs (science / law / business) ---
    r"published|released|launched|signed|appointed|approved|rejected|"
    r"proposed|concluded|demonstrated|established|announced|completed|"
    r"introduced|implemented|adopted|founded|passed|produced|caused|"
    r"developed|created|built|designed|proved|showed|identified|"
    r"removed|replaced|expanded|reduced|increased|decreased|achieved|"
    r"committed|pledged|promised|vowed|raised|tightened|loosened|"
    r"collapsed|withdrew|rejoined|ratified|responded|concluded|merged"
    r")\b",
    re.IGNORECASE,
)

# Module-level fallback protagonist pattern: any capitalized word of 3+ chars.
# Replaced per-document by _extractDocumentEntities() in the arc-aware path.
_PROTAGONIST_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")


_STATIVE_VERB_RE = re.compile(
    r"\b(?:remained|stayed|sat|stood|waited|rested|paused|stopped|halted|lingered)\b",
    re.IGNORECASE,
)

# Concrete outcome signals: sentences with these patterns describe *results*
# (approvals, verdicts, measurements, conclusions) not just events.
# These sentences are often under-selected by centrality scoring because
# they use specific numbers and named outcomes that appear only once,
# giving them low cosine similarity to other sentences in the document.
# The OUTCOME_BOOST multiplier counters this by lifting their score.
_OUTCOME_SIGNAL_RE = re.compile(
    r"\b(?:"
    # regulatory / legal outcomes
    r"approved|ruled|ordered|awarded|sentenced|found guilty|dismissed|upheld|"
    r"granted|denied|overturned|acquitted|convicted|fined|banned|"
    # scientific / clinical conclusions
    r"demonstrated|confirmed|showed that|proved|concluded that|found that|"
    r"reduced by|increased by|improved by|decreased by|fell by|rose by|"
    r"reached \d|exceeded \d|grew from|dropped from|"
    # policy / business outcomes
    r"passed the|signed the|enacted|ratified|adopted the|launched the|"
    r"called for|phase-down|phase out|"
    r"committed to|pledged to|agreed to|reached an agreement|"
    # named numerical outcomes
    r"\d+\s*(?:percent|%|million|billion|trillion|months|years|days|degrees)|in \d{4}\b"
    r")\b",
    re.IGNORECASE,
)

# Score multiplier applied to sentences matching _OUTCOME_SIGNAL_RE.
# Raises outcome sentences into competition with high-centrality setup sentences.
# 1.6 was chosen so an outcome sentence with moderate IDF beats a pure-context
# sentence with high centrality, without completely overriding IDF signal.
WEIGHT_OUTCOME_SIGNAL: float = 1.6


def _narrativeWeight(sentence: str, entityPattern: re.Pattern[str] = _PROTAGONIST_RE) -> float:
    """Multiplier applied to TF-IDF centrality score before selection.

    Rewards: named entities (1.4x), plot-action verbs (1.5x), outcome signals (1.6x).
    Penalises: pure dialogue attribution (WEIGHT_DIALOGUE_SENTENCE).
    Outcome signals are boosted independently so resolution sentences compete with
    high-centrality setup sentences that would otherwise dominate.
    """
    weight = 1.0
    if _DIALOGUE_RE.search(sentence):
        return WEIGHT_DIALOGUE_SENTENCE
    if entityPattern.search(sentence):
        weight *= 1.4
    if _PLOT_VERB_RE.search(sentence):
        weight *= 1.5
    if _OUTCOME_SIGNAL_RE.search(sentence):
        weight *= WEIGHT_OUTCOME_SIGNAL
    return weight


# ---------------------------------------------------------------------------
# Document-driven named entity extractor
# ---------------------------------------------------------------------------


def _extractDocumentEntities(
    sentences: list[str],
    idf: dict[str, float],
    min_freq: int = 3,
) -> re.Pattern[str]:
    """Build a regex matching the document's most important named entities.

    A named entity is any capitalized multi-character token that:
    - Appears in >= effective_min_freq distinct sentences
      (effective_min_freq scales with document size)
    - Is NOT in the common-openers / generic-word exclusion list
    - Appears more often than would be expected for a generic discourse word
      (uses relative sentence frequency as a proxy for 'specificity')

    Returns a compiled regex pattern matching any of these entities as whole words.
    Falls back to a pattern that matches any capitalized 3+ char word if too few
    entities are found.
    """
    n_sentences = max(len(sentences), 1)
    effective_min = max(min_freq, n_sentences // ENTITY_FREQ_PER_SENTENCE)

    # Count how many distinct sentences each capitalised token appears in.
    # Crucially: only count occurrences that are NOT at the start of a sentence
    # (sentence-initial capitals are often just capitalization, not proper nouns).
    # We use a sliding check: token must appear capitalized somewhere after the
    # first word of the sentence.
    mid_sent_freq: dict[str, int] = {}
    for sentence in sentences:
        words = sentence.split()
        # Check all words except the first for mid-sentence capitalisation
        seen_in_sent: set[str] = set()
        for w in words[1:]:
            token = re.match(r"^([A-Z][a-z]{2,})\b", w)
            if token:
                t = token.group(1)
                if t not in _ENTITY_OPENERS and t.lower() not in _STOPWORDS:
                    seen_in_sent.add(t)
        for t in seen_in_sent:
            mid_sent_freq[t] = mid_sent_freq.get(t, 0) + 1

    candidates = {t: c for t, c in mid_sent_freq.items() if c >= effective_min}

    if not candidates:
        return re.compile(r"\b[A-Z][a-z]{2,}\b")

    # Filter 2: exclude tokens whose lowercase form is an English stopword
    # (catches words like "Into", "From" that pass the opener check but are
    # clearly function words when lowercased).
    candidates = {t: c for t, c in candidates.items() if t.lower() not in _STOPWORDS}

    # Filter 3: use sentence-frequency relative rank.
    # Keep the top half by sentence-frequency to prioritise primary entities
    # (main characters, key locations) over minor ones.
    if len(candidates) > 6:
        threshold = sorted(candidates.values())[len(candidates) // 2]
        candidates = {t: c for t, c in candidates.items() if c >= threshold}

    entities = sorted(candidates.keys())

    if len(entities) < 3:
        # Fallback: any capitalized word of 3+ chars
        return re.compile(r"\b[A-Z][a-z]{2,}\b")

    return re.compile(
        r"\b(?:" + "|".join(re.escape(e) for e in entities) + r")\b",
        re.IGNORECASE,
    )


# ---------------------------------------------------------------------------
# Structural event detection (domain-independent)
# ---------------------------------------------------------------------------


def _detectStructuralEvents(
    sentences: list[str],
    idf: dict[str, float],
    entityPattern: re.Pattern[str],
    n_arcs: int = 4,
) -> list[tuple[int, str, str]]:
    """Detect structurally important event sentences without domain knowledge.

    An event sentence must:
      1. Contain a named entity (entityPattern)
      2. Contain a past-tense plot verb (_PLOT_VERB_RE)
      3. Not be dialogue (_DIALOGUE_RE)
      4. Not be stative-only without a plot verb

    Returns at most one event per document slice, with n_arcs slices total.
    Using n_arcs (not hardcoded 4) ensures short docs use 2-3 slices not 4.
    Result list is sorted by sentence index (narrative order).
    """
    n = len(sentences)
    if n == 0:
        return []

    def _score(s: str) -> float:
        if _DIALOGUE_RE.search(s):
            return 0.0
        if not entityPattern.search(s):
            return 0.0
        if not _PLOT_VERB_RE.search(s):
            return 0.0
        if s.count("'") + s.count('"') > 2:
            return 0.0  # dialogue bleed
        names = set(m.lower() for m in entityPattern.findall(s))
        ed = len(names) / max(len(s.split()), 1)
        pw = WEIGHT_PLOT_VERB if _PLOT_VERB_RE.search(s) else 1.0
        if _STATIVE_VERB_RE.search(s):
            pw = WEIGHT_STATIVE_VERB
        if _OUTCOME_SIGNAL_RE.search(s):
            pw *= WEIGHT_OUTCOME_SIGNAL
        tokens = _tokenize(s)
        idfAvg = sum(idf.get(t, 1.0) for t in tokens) / max(len(tokens), 1)
        wc = len(s.split())
        lb = (
            WEIGHT_SHORT_SENTENCE
            if wc < SHORT_SENTENCE_WORDS
            else (
                WEIGHT_SWEET_SENTENCE
                if wc <= SWEET_SENTENCE_WORDS
                else (WEIGHT_LONG_SENTENCE if wc > LONG_SENTENCE_WORDS else 1.0)
            )
        )
        return (1.0 + ed * ENTITY_DENSITY_SCALE) * pw * idfAvg * lb

    # Roles for each arc slice (use as many as n_arcs allows)
    _all_roles = ["setup", "complication", "crisis", "resolution"]
    quartile_roles = _all_roles[:n_arcs] + _all_roles[-1:] * max(0, n_arcs - 4)
    quartile_best: dict[int, tuple[float, int, str]] = {}

    for idx, s in enumerate(sentences):
        sc = _score(s)
        if sc == 0.0:
            continue
        # Require at least 2 distinct named entities for higher story signal.
        # Single-entity sentences can be scene-setting rather than plot events.
        names = set(m.lower() for m in entityPattern.findall(s))
        if len(names) < 2:
            # Allow single-entity sentences only if they have above-average IDF
            tokens = _tokenize(s)
            avg_idf = sum(idf.get(t, 1.0) for t in tokens) / max(len(tokens), 1)
            if avg_idf < MIN_SINGLE_ENTITY_IDF:
                continue
        quartile = min(n_arcs - 1, int(idx * n_arcs / max(n, 1)))
        if quartile not in quartile_best or sc > quartile_best[quartile][0]:
            quartile_best[quartile] = (sc, idx, s)

    result: list[tuple[int, str, str]] = []
    for q in sorted(quartile_best.keys()):
        _sc, idx, s = quartile_best[q]
        role = quartile_roles[q]
        result.append((idx, role, s))

    # If the first elected sentence is far from the document start (>30%),
    # prepend the first qualifying sentence from the opening 20% as a topical
    # anchor.  This ensures the key subject is always introduced.
    # Only fires when the gap is significant; avoids displacing a good Q0 winner.
    if result:
        first_result_idx = min(r[0] for r in result)
        anchor_gap = max(1, int(n * 0.30))  # gap threshold
        first_cutoff = max(1, int(n * 0.20))  # search window
        if first_result_idx >= anchor_gap:
            for idx, s in enumerate(sentences[:first_cutoff]):
                sc = _score(s)
                if sc > 0.0:
                    result.insert(0, (idx, "setup", s))
                    break

    return result


# ---------------------------------------------------------------------------
# Arc-aware best-sentence election
# ---------------------------------------------------------------------------


def _electArcSentence(
    sentences: list[str],
    global_idf: dict[str, float],
    claimedEvents: set[str],
    entityPattern: re.Pattern[str] = _PROTAGONIST_RE,
) -> str:
    """Return the best narrative sentence from a story arc.

    Priority order:
      1. Highest entity-density x plot-verb x IDF score among non-dialogue sentences.
      2. Fallback: any sentence by base score.

    claimedEvents is accepted for API compatibility but is not mutated here
    (event-pattern matching has been replaced by structural detection).
    """
    if not sentences:
        return ""
    if len(sentences) == 1:
        return sentences[0]

    n = len(sentences)

    def _entityDensity(sentence: str) -> float:
        matches = set(m.lower() for m in entityPattern.findall(sentence))
        words = sentence.split()
        return len(matches) / len(words) if words else 0.0

    def _plotWeight(sentence: str) -> float:
        if _DIALOGUE_RE.search(sentence):
            return WEIGHT_DIALOGUE_SENTENCE
        if sentence.count("'") + sentence.count('"') > 2:
            return WEIGHT_DIALOGUE_BLEED
        if _STATIVE_VERB_RE.search(sentence) and not _PLOT_VERB_RE.search(sentence):
            return WEIGHT_STATIVE_VERB
        if _PLOT_VERB_RE.search(sentence):
            return WEIGHT_PLOT_VERB
        return 1.0

    def _idfScore(sentence: str) -> float:
        tokens = _tokenize(sentence)
        if not tokens:
            return 0.0
        return sum(global_idf.get(t, 1.0) for t in tokens) / len(tokens)

    def _positionBoost(idx: int) -> float:
        return POS_BOOST_START + (POS_BOOST_END - POS_BOOST_START) * (idx / max(n - 1, 1))

    def _lengthBoost(sentence: str) -> float:
        wc = len(sentence.split())
        if wc < SHORT_SENTENCE_WORDS:
            return WEIGHT_SHORT_SENTENCE
        if wc <= SWEET_SENTENCE_WORDS:
            return WEIGHT_SWEET_SENTENCE
        if wc > LONG_SENTENCE_WORDS:
            return WEIGHT_LONG_SENTENCE
        return 1.0

    def _baseScore(i: int) -> float:
        s = sentences[i]
        return (
            (1.0 + _entityDensity(s) * ENTITY_DENSITY_SCALE)
            * _plotWeight(s)
            * _idfScore(s)
            * _positionBoost(i)
            * _lengthBoost(s)
        )

    # Best non-dialogue sentence by base score
    bestIdx = max(range(n), key=_baseScore)
    return sentences[bestIdx]


# ---------------------------------------------------------------------------
# Clause distillation and narrative role inference
# ---------------------------------------------------------------------------


def _distillClause(sentence: str, entityPattern: re.Pattern[str] = _PROTAGONIST_RE) -> str:
    """Strip heavy temporal/adverbial preamble; keep the core narrative clause.

    Outcome sentences (those matching _OUTCOME_SIGNAL_RE) are never truncated --
    their specific numbers, names, and verdicts are the point.
    All other sentences: preserve if <=22 words, otherwise extract the first
    sub-clause that contains a named entity or plot verb.
    """
    words = sentence.split()
    if not words:
        return sentence

    # Never truncate outcome sentences -- the specific figures ARE the content
    if _OUTCOME_SIGNAL_RE.search(sentence):
        core = sentence.strip()
        core = core[0].upper() + core[1:]
        if not core.rstrip().endswith((".", "!", "?")):
            core = core.rstrip() + "."
        return core

    if len(words) <= 22:
        core = sentence.strip()
        core = core[0].upper() + core[1:]
        if not core.rstrip().endswith((".", "!", "?")):
            core = core.rstrip() + "."
        return core

    leading_sub = re.match(
        r"^((?:When|At|After|Before|As|Once|Until|While|Though|Although|If|Since)\b[^,;]{5,50}),\s+(.+)$",
        sentence,
        re.IGNORECASE,
    )
    if leading_sub:
        sub_clause = leading_sub.group(1).strip()
        main_clause = leading_sub.group(2).strip()
        sub_has_signal = bool(entityPattern.search(sub_clause) or _PLOT_VERB_RE.search(sub_clause))
        main_has_signal = bool(entityPattern.search(main_clause) or _PLOT_VERB_RE.search(main_clause))
        if sub_has_signal and not main_has_signal:
            core = sub_clause
        elif main_has_signal and len(main_clause.split()) <= 18:
            core = main_clause
        else:
            core = sub_clause if sub_has_signal else main_clause
        core = core[0].upper() + core[1:]
        if not core.rstrip().endswith((".", "!", "?")):
            core = core.rstrip() + "."
        return core

    if ";" in sentence:
        core = sentence.split(";")[0].strip()
        core = core[0].upper() + core[1:]
        if not core.rstrip().endswith((".", "!", "?")):
            core = core.rstrip() + "."
        if len(core.split()) <= 30:
            return core

    core = " ".join(words[:25])
    core = core[0].upper() + core[1:]
    if not core.rstrip().endswith((".", "!", "?")):
        core = core.rstrip() + "."
    return core


def _inferNarrativeRole(sentence: str, arcIdx: int, n_arcs: int) -> str:
    """Classify a sentence into setup / complication / crisis / resolution.

    Arc position is the primary signal (works for all document types).
    The lexical overrides use domain-agnostic English patterns only --
    no fiction vocabulary.
    """
    s_lower = sentence.lower()

    # Resolution: conclusive / positive-outcome language
    if any(
        w in s_lower
        for w in (
            "at last",
            "in the end",
            "finally",
            "came back",
            "was over",
            "had ended",
            "was complete",
            "was resolved",
            "was achieved",
            "was restored",
            "was established",
        )
    ):
        return "resolution"

    # Crisis: loss / failure / danger / isolation
    if any(
        w in s_lower
        for w in (
            "was lost",
            "was destroyed",
            "was killed",
            "had failed",
            "could not escape",
            "was trapped",
            "no longer",
            "collapsed",
            "was abandoned",
        )
    ):
        return "crisis"

    # Complication: obstacle / reversal / unexpected difficulty
    if any(
        w in s_lower
        for w in (
            "however",
            "nevertheless",
            "despite",
            "failed to",
            "could not",
            "was unable",
            "was prevented",
            "was blocked",
            "went wrong",
            "was interrupted",
            "was delayed",
        )
    ):
        return "complication"

    # Fallback: divide document into four equal bands by arc position
    progress = arcIdx / max(n_arcs - 1, 1)
    if progress < ARC_ROLE_SETUP_END:
        return "setup"
    if progress < ARC_ROLE_COMPLICATION_END:
        return "complication"
    if progress < ARC_ROLE_CRISIS_END:
        return "crisis"
    return "resolution"


# ---------------------------------------------------------------------------
# Structural event clause composer (domain-independent)
# ---------------------------------------------------------------------------


def _composeEventClause(
    sentence: str,
    role: str,
    entityPattern: re.Pattern[str] = _PROTAGONIST_RE,
) -> str:
    """Compose a declarative clause from an event sentence, without domain templates.

    For sentences <= 22 words, returns the distilled clause directly (it's already
    clean enough).

    For longer sentences, applies extraction:
    1. Extract the primary agent: first named entity match that is NOT a common
       opener/function word.
    2. Extract the action: the plot verb and up to 8 words following it.
    3. Compose as: "{Agent} {action-phrase}."

    Falls back to _distillClause(sentence) if extraction is ambiguous or the
    composed result would be shorter than 5 words.
    """
    distilled = _distillClause(sentence, entityPattern)

    # For short sentences, the distilled form is already good.
    words = sentence.split()
    if len(words) <= 22:
        return distilled

    # Step 1: find primary agent -- first named entity not in opener/stopword list.
    # We search for the pattern but skip matches that are plain function words.
    agent = ""
    for m in entityPattern.finditer(sentence):
        candidate = m.group(0)
        # Skip if it's clearly a generic/function word even if it matches pattern
        if candidate in _ENTITY_OPENERS or candidate.lower() in _STOPWORDS:
            continue
        # Skip very short matches that are likely abbreviations
        if len(candidate) < 3:
            continue
        agent = candidate
        break

    if not agent:
        return distilled

    # Step 2: find plot verb
    verb_match = _PLOT_VERB_RE.search(sentence)
    if not verb_match:
        return distilled

    verb_start = verb_match.start()
    after_verb = sentence[verb_start:]
    # Take verb + up to 8 words, but stop at a comma or semicolon
    after_verb_clean = re.split(r"[,;]", after_verb, maxsplit=1)[0]
    action_words = after_verb_clean.split()[:9]
    action_phrase = " ".join(action_words).rstrip()

    # Step 3: compose and normalise
    result = f"{agent} {action_phrase}"
    result = result.strip()
    if len(result.split()) < 4:
        return distilled

    result = result[0].upper() + result[1:]
    if not result.endswith((".", "!", "?")):
        result = result.rstrip() + "."

    return result


# ---------------------------------------------------------------------------
# Bridge lookup (domain-independent -- uses abstract role names)
# ---------------------------------------------------------------------------

_ROLE_BRIDGES: dict[tuple[str, str], tuple[str, bool]] = {
    ("setup", "setup"): ("and", False),
    ("setup", "complication"): ("but", False),
    ("setup", "crisis"): ("until", False),
    ("setup", "resolution"): ("At last,", True),
    ("complication", "setup"): ("Meanwhile,", True),
    ("complication", "complication"): ("while", False),
    ("complication", "crisis"): ("until", False),
    ("complication", "resolution"): ("Yet in the end,", True),
    ("crisis", "setup"): ("Though", True),
    ("crisis", "complication"): ("but", False),
    ("crisis", "crisis"): ("and", False),
    ("crisis", "resolution"): ("until at last", False),
    ("resolution", "resolution"): (";", False),
    ("resolution", "complication"): ("but", False),
    ("resolution", "crisis"): ("before", False),
}

# Kept for API compatibility; structural events now use role-based bridges only.
_EVENT_BRIDGES: dict[tuple[str, str], tuple[str, bool]] = {}

_ROLE_CONNECTOR_MAP: dict[str, str] = {
    "setup": "and",
    "complication": "but",
    "crisis": "until",
    "resolution": "at last",
}


def _getBridge(ev_a: str, ev_b: str, role_a: str, role_b: str) -> tuple[str, bool]:
    """Return (connector_string, starts_new_sentence) for the transition between two events."""
    bridge = _ROLE_BRIDGES.get((role_a, role_b))
    if bridge:
        return bridge
    return ("then", False)


def _composeNarrative(
    arcSentences: list[str],
    arcEvents: list[str],
    max_words: int,
    entityPattern: re.Pattern[str] = _PROTAGONIST_RE,
) -> str:
    """Compose a flowing prose narrative from elected arc sentences.

    This is TinyToT's structural composition layer:
      1. For each elected sentence, apply _composeEventClause to produce a
         declarative composed clause based on entity + verb extraction.
      2. Determine the causal bridge between consecutive clauses via role.
      3. Assemble into multi-sentence prose with proper punctuation.

    The output reads like a human-written summary because the structural
    patterns encode narrative shape, not domain-specific knowledge.
    """
    if not arcSentences:
        return ""

    n_arcs = len(arcSentences)
    word_limit = int(max_words * STITCH_OVERSHOOT)
    roles = [_inferNarrativeRole(arcSentences[i], i, n_arcs) for i in range(n_arcs)]

    # Only apply structural composition when we have real document-specific entities.
    # The generic fallback pattern (\b[A-Z][a-z]{2,}\b) matches any capitalized word,
    # so agent extraction would pick sentence-openers like "Global" or "The" as agents.
    has_specific_entities = entityPattern.pattern != r"\b[A-Z][a-z]{2,}\b"

    clauses = [
        _composeEventClause(arcSentences[i], roles[i], entityPattern)
        if has_specific_entities
        else _distillClause(arcSentences[i], entityPattern)
        for i in range(n_arcs)
    ]

    result_sentences: list[str] = []
    current = clauses[0].rstrip(".!?")

    for i in range(1, len(clauses)):
        connector, new_sentence = _getBridge(
            arcEvents[i - 1] if i - 1 < len(arcEvents) else "",
            arcEvents[i] if i < len(arcEvents) else "",
            roles[i - 1],
            roles[i],
        )

        clause = clauses[i].rstrip(".!?")
        # Strip leading conjunction from clause to avoid double-connectors
        clause = re.sub(
            r"^(?:But|And|Yet|Or|Nor|So|When|While|Though|Although|Until|Since|As|Then)\s+",
            "",
            clause,
            flags=re.IGNORECASE,
        )
        clause = clause[0].upper() + clause[1:] if clause else clause

        if new_sentence or connector == ";":
            result_sentences.append(current.rstrip() + ".")
            if connector == ";":
                current = clause
            else:
                conn_cap = connector.rstrip(",").capitalize()
                lower_clause = clause[0].lower() + clause[1:] if clause and not entityPattern.match(clause) else clause
                current = conn_cap + " " + lower_clause
        else:
            lower_clause = clause[0].lower() + clause[1:] if clause and not entityPattern.match(clause) else clause
            current = current + " " + connector + " " + lower_clause

        projected = sum(len(s.split()) for s in result_sentences) + len((current + ".").split())
        if projected > word_limit:
            break

    final = current.rstrip()
    if not final.endswith((".", "!", "?")):
        final += "."
    result_sentences.append(final)

    full = " ".join(result_sentences)
    words = full.split()
    if len(words) > word_limit:
        words = words[:word_limit]
        full = " ".join(words)
        if not full.endswith((".", "!", "?")):
            full = full.rstrip() + "."

    return full


# Keep _stitchArcs as alias so existing short-doc path still compiles
def _stitchArcs(arcSentences: list[str], arcEvents: list[str], max_words: int) -> str:
    return _composeNarrative(arcSentences, arcEvents, max_words)


# ---------------------------------------------------------------------------
# Greedy word-budget selection (kept for short-doc path)
# ---------------------------------------------------------------------------


def _selectByWordBudget(
    sentences: list[str],
    scores: list[float],
    max_words: int,
) -> list[str]:
    """Select highest-scoring sentences within the word budget, preserving order."""
    ranked = sorted(
        range(len(sentences)),
        key=lambda i: scores[i] * _narrativeWeight(sentences[i]),
        reverse=True,
    )
    chosen: set[int] = set()
    seen_normalized: set[str] = set()
    word_count = 0
    for idx in ranked:
        normalised = " ".join(sentences[idx].lower().split())
        if normalised in seen_normalized:
            continue
        wc = len(sentences[idx].split())
        if word_count + wc <= max_words:
            chosen.add(idx)
            seen_normalized.add(normalised)
            word_count += wc
        if word_count >= max_words * BUDGET_FILL_FRACTION:
            break
    return [sentences[i] for i in sorted(chosen)]


# ---------------------------------------------------------------------------
# Single-pass summarisation (short documents)
# ---------------------------------------------------------------------------


def _summarisePassage(sentences: list[str], max_words: int) -> str:
    """Summarise a list of sentences to at most max_words words."""
    if not sentences:
        return ""
    vectors, _ = _buildTfIdf(sentences)
    scores = _scoreByLexicalCentrality(vectors)
    selected = _selectByWordBudget(sentences, scores, max_words)
    return " ".join(selected)


# ---------------------------------------------------------------------------
# Arc-aware summarisation for long documents (novels, reports)
# ---------------------------------------------------------------------------


def _arcAwareSummarise(
    sentences: list[str],
    max_words: int,
    n_arcs: int = NARRATIVE_ARCS,
) -> str:
    """Summarise a document via two-pass structural arc election.

    Adapts the number of arcs to document length so short passages (news articles,
    abstracts) don't get 4 arcs crammed into 50 words:
      < 20 sentences  -> 2 arcs (setup + resolution)
      20-49 sentences -> 3 arcs (setup + body + resolution)
      50+ sentences   -> 4 arcs (setup / complication / crisis / resolution)
    """
    n_sentences = len(sentences)
    if n_arcs == NARRATIVE_ARCS:  # only adapt when using the default
        if n_sentences < 8:
            n_arcs = 2
        elif n_sentences < 50:
            n_arcs = 3

    n = len(sentences)

    front_skip = max(0, int(n * SKIP_FRONT_FRACTION))
    back_skip = max(0, int(n * SKIP_BACK_FRACTION))
    body = sentences[front_skip : n - back_skip] if back_skip else sentences[front_skip:]
    nb = len(body)
    if nb < n_arcs:
        body = sentences
        nb = len(body)

    sample_step = max(1, nb // IDF_SAMPLE_MAX)
    sample = body[::sample_step]
    _, global_idf = _buildTfIdf(sample)

    # Build document-specific entity pattern
    entityPattern = _extractDocumentEntities(body, global_idf)

    # Scoring helpers (used in both passes)
    def _baseScore(s: str) -> float:
        if _DIALOGUE_RE.search(s):
            return 0.0
        names = set(m.lower() for m in entityPattern.findall(s))
        ed = len(names) / max(len(s.split()), 1)
        if s.count("'") + s.count('"') > 2:
            pw = WEIGHT_DIALOGUE_BLEED
        elif _STATIVE_VERB_RE.search(s) and not _PLOT_VERB_RE.search(s):
            pw = WEIGHT_STATIVE_VERB
        elif _PLOT_VERB_RE.search(s):
            pw = WEIGHT_PLOT_VERB
        else:
            pw = 1.0
        if _OUTCOME_SIGNAL_RE.search(s):
            pw *= WEIGHT_OUTCOME_SIGNAL
        tokens = _tokenize(s)
        idf = sum(global_idf.get(t, 1.0) for t in tokens) / max(len(tokens), 1)
        wc = len(s.split())
        lb = 0.6 if wc < 8 else (1.2 if wc <= 18 else (0.7 if wc > 25 else 1.0))
        return (1.0 + ed * 6.0) * pw * idf * lb

    arc_size = max(1, nb // n_arcs)

    # Pass 1: detect structural events per quartile.
    # For long documents (novels, reports with preamble) skip the opening
    # front matter and closing appendices.  For short documents (<100 sentences)
    # scan the full body -- every sentence may carry key information.
    MIN_SENTENCES_FOR_SKIP = 100
    if nb >= MIN_SENTENCES_FOR_SKIP:
        narrative_start = max(0, int(nb * NARRATIVE_SKIP_FRONT))
        narrative_end = min(nb, int(nb * (1.0 - NARRATIVE_SKIP_BACK)))
    else:
        narrative_start = 0
        narrative_end = nb
    narrative_body = body[narrative_start:narrative_end]

    structural_events = _detectStructuralEvents(narrative_body, global_idf, entityPattern, n_arcs)

    # Map detected events into arcs (by quartile -> arc index proportionally)
    event_arc_sentences: list[tuple[int, str, str]] = []  # (arcIdx, sentence, role)
    for ev_idx, ev_role, ev_sent in structural_events:
        # Map narrative body index back to full body index
        full_idx = narrative_start + ev_idx
        # Assign to arc by proportional position
        arcIdx = min(n_arcs - 1, int(full_idx * n_arcs / max(nb, 1)))
        event_arc_sentences.append((arcIdx, ev_sent, ev_role))

    assigned_arcs = {arcIdx for arcIdx, _, _ in event_arc_sentences}
    claimedEvents: set[str] = set()

    # Pass 2: fill remaining arcs with best positional sentences
    for arcIdx in range(n_arcs):
        if arcIdx in assigned_arcs:
            continue
        start = arcIdx * arc_size
        end = start + arc_size if arcIdx < n_arcs - 1 else nb
        arc = body[start:end]
        if arcIdx >= 2 and len(arc) > 20:
            arc = arc[len(arc) // 2 :]
        elected = _electArcSentence(arc, global_idf, claimedEvents, entityPattern)
        if elected:
            event_arc_sentences.append((arcIdx, elected, ""))

    # Sort all by arc index to get narrative order
    event_arc_sentences.sort(key=lambda x: x[0])

    arcSentences: list[str] = []
    arcEvents: list[str] = []
    seen: set[str] = set()
    for _, s, role in event_arc_sentences:
        key = " ".join(s.lower().split())
        if key not in seen:
            seen.add(key)
            arcSentences.append(s)
            arcEvents.append(role)

    return _composeNarrative(arcSentences, arcEvents, max_words, entityPattern)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def summarizeDocument(
    text: str,
    max_words: int = 50,
    chunk_size: int = CHUNK_SENTENCES,
    inter_words: int = INTER_WORDS,
) -> str:
    """Summarise *text* to at most *max_words* words using extractive TF-IDF.

    For short texts (< ARC_THRESHOLD sentences) standard extractive selection is used.
    For long texts (novels, reports) arc-aware election picks the best sentence from
    each narrative quarter (setup / rising / climax / resolution) and stitches them
    into a flowing prose summary.

    Args:
        text:       Full document text.
        max_words:  Word budget for the final summary.
        chunk_size: Unused (kept for API compatibility).
        inter_words: Unused (kept for API compatibility).

    Returns:
        Summary string of at most *max_words* words.

    Example::
        >>> text = open("lotr.txt").read()
        >>> print(summarizeDocument(text, max_words=50))
    """
    if not text.strip():
        return ""
    sentences = _splitSentences(text)
    if not sentences:
        sentences = [p.strip() for p in text.split("\n\n") if p.strip()]

    if len(sentences) >= ARC_THRESHOLD:
        return _arcAwareSummarise(sentences, max_words)

    return _summarisePassage(sentences, max_words)


def summarizeFile(
    path: str | Path,
    max_words: int = 50,
    encoding: str = "utf-8",
) -> str:
    """Read a file from *path* and return a *max_words*-word extractive summary.

    Args:
        path:      Path to any plain-text file (.txt, .md, .rst, etc.).
        max_words: Word budget for the final summary.
        encoding:  File encoding (default utf-8).

    Returns:
        Summary string of at most *max_words* words, or an error message.
    """
    p = Path(path).expanduser()
    if not p.exists():
        return f"File not found: {path}"
    try:
        text = p.read_text(encoding=encoding, errors="replace")
    except Exception as exc:
        return f"Could not read file: {exc}"
    return summarizeDocument(text, max_words=max_words)

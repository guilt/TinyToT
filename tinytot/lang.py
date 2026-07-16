"""
tinytot.lang — Shared language constants.

Single source of truth for language codes, script detection, social phrases,
and translation pack configuration. Compatible with Python 3.8+.

Usage::

    from tinytot.lang import Lang, detect_lang, TRANSLATE_PAIRS, SOCIAL_PATTERN

    Lang.KOREAN.code              # "ko"
    Lang.KOREAN.label             # "Korean"
    Lang.KOREAN.social_phrases    # ["안녕", "감사", ...]
    Lang.from_name("korean")      # Lang.KOREAN
    Lang.from_code("ko")          # Lang.KOREAN
    detect_lang("안녕하세요")      # Lang.KOREAN
    SOCIAL_PATTERN.match("hello") # match object
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional, Pattern, Tuple

# ---------------------------------------------------------------------------
# Script detection ranges: (start_char, end_char, iso_code).
# Ordered from most specific to least to avoid false positives.
# ---------------------------------------------------------------------------
_SCRIPT_RANGES: List[Tuple[str, str, str]] = [
    ("가", "힣", "ko"),  # Hangul syllables
    ("一", "鿿", "zh"),  # CJK Unified Ideographs
    ("぀", "ヿ", "ja"),  # Hiragana + Katakana
    ("؀", "ۿ", "ar"),  # Arabic
    ("ऀ", "ॿ", "hi"),  # Devanagari (Hindi)
    ("Ѐ", "ӿ", "ru"),  # Cyrillic (Russian)
    ("Ͱ", "Ͽ", "el"),  # Greek
    ("฀", "๿", "th"),  # Thai
    ("֐", "׿", "he"),  # Hebrew
]


class Lang(Enum):
    """ISO 639-1 language codes with human-readable labels and social phrases.

    Each member's value is the ISO 639-1 code string.
    ``social_phrases`` lists common greetings/farewells/pleasantries in that
    language — used to build SOCIAL_PATTERN for small-talk detection.
    """

    # fmt: off
    ARABIC     = "ar"
    CHINESE    = "zh"
    DANISH     = "da"
    DUTCH      = "nl"
    ENGLISH    = "en"
    FINNISH    = "fi"
    FRENCH     = "fr"
    GERMAN     = "de"
    GREEK      = "el"
    HEBREW     = "he"
    HINDI      = "hi"
    INDONESIAN = "id"
    ITALIAN    = "it"
    JAPANESE   = "ja"
    KOREAN     = "ko"
    NORWEGIAN  = "no"
    POLISH     = "pl"
    PORTUGUESE = "pt"
    RUSSIAN    = "ru"
    SPANISH    = "es"
    SWEDISH    = "sv"
    THAI       = "th"
    TURKISH    = "tr"
    VIETNAMESE = "vi"
    # fmt: on

    @property
    def code(self) -> str:
        """ISO 639-1 code, e.g. 'ko'."""
        return self.value

    @property
    def label(self) -> str:
        """Display name, e.g. 'Korean'."""
        return self.name.capitalize()

    @property
    def social_phrases(self) -> List[str]:
        """Common greetings, farewells, and pleasantries in this language.

        Each entry is a regex fragment (word-boundary anchoring applied later).
        Extend a language's list to improve small-talk detection coverage.
        """
        return _SOCIAL_PHRASES.get(self, [])

    @classmethod
    def from_name(cls, name: str) -> Optional["Lang"]:
        """Look up by English name (case-insensitive). Returns None if not found."""
        return _NAME_TO_LANG.get(name.lower())

    @classmethod
    def from_code(cls, code: str) -> Optional["Lang"]:
        """Look up by ISO code (case-insensitive). Returns None if not found."""
        return _CODE_TO_LANG.get(code.lower())


# ---------------------------------------------------------------------------
# Social phrases data — keyed by Lang member.
# Latin-script entries use word-boundary anchors (\b) in the compiled pattern.
# Non-Latin entries are matched as literal substrings (no \b needed).
# Add new phrases here; SOCIAL_PATTERN is rebuilt automatically at import time.
# ---------------------------------------------------------------------------

_SOCIAL_PHRASES: Dict[Lang, List[str]] = {
    Lang.ENGLISH: [
        r"hi",
        r"hello",
        r"hey",
        r"howdy",
        r"hiya",
        r"good\s+(?:morning|evening|afternoon|night|day)",
        r"how\s+are\s+you",
        r"how\s+do\s+you\s+do",
        r"how.s\s+it\s+going",
        r"nice\s+to\s+(?:meet|see)\s+you",
        r"pleased\s+to\s+meet",
        r"thanks?(?:\s+you)?",
        r"thank\s+you",
        r"cheers",
        r"appreciate\s+(?:it|that)",
        r"bye",
        r"goodbye",
        r"see\s+you",
        r"take\s+care",
        r"farewell",
        r"who\s+are\s+you",
        r"what\s+are\s+you",
        r"introduce\s+yourself",
        r"what\s+can\s+you\s+(?:do|help\s+(?:me\s+)?with)",
        r"your\s+(?:name|capabilities)",
        r"are\s+you\s+an?\s+(?:ai|bot|assistant|robot|model|llm)",
        r"tell\s+me\s+a\s+joke",
        r"tell\s+me\s+something\s+funny",
        r"what\s+is\s+the\s+meaning\s+of\s+life",
        r"i\s+(?:am|feel|feel|'m|'m)\s+(?:feeling\s+)?(?:sad|happy|tired|bored|excited|great|ok|okay|good|fine|well|fantastic|amazing|terrible|awful)",
        r"who\s+(?:made|created|built|invented|designed)\s+you",
        r"are\s+you\s+(?:conscious|sentient|alive|real|human)",
        r"do\s+you\s+(?:have\s+feelings|feel|dream|think|have\s+emotions)",
        r"what.s\s+your\s+(?:favourite|favorite)\s+\w+",
        r"can\s+you\s+keep\s+a\s+secret",
        r"tell\s+me\s+a\s+fun\s+fact",
        r"are\s+you\s+better\s+than\s+\w+",
        r"i.m\s+(?:bored|stressed|tired|happy|sad|lonely|excited|nervous|anxious|frustrated)",
        r"that.s\s+(?:wrong|incorrect|right|correct|amazing|great|awesome|terrible|bad|good)",
        r"you.re\s+(?:really\s+)?(?:helpful|amazing|great|awesome|wrong|right|incorrect)",
        r"do\s+you\s+dream",
        # Roleplay / persona
        r"(?:can\s+you\s+)?(?:pretend|roleplay|role-play|act|play)\s+(?:to\s+be\s+|as\s+|like\s+)?(?:a\s+|an\s+)?\w+",
        r"be\s+my\s+(?:tutor|teacher|mentor|coach|friend|buddy|assistant|companion|partner)",
        r"(?:let.s|lets)\s+(?:roleplay|role.play|pretend|play)",
        r"you\s+are\s+(?:now\s+)?(?:a\s+|an\s+|my\s+)?\w+",
        # Relationship / emotional
        r"i\s+(?:love|like|adore|appreciate|enjoy|miss)\s+you",
        r"you\s+(?:are|'re)\s+(?:my\s+)?(?:favourite|favorite|amazing|awesome|great|wonderful|the\s+best)",
        r"can\s+we\s+be\s+friends",
        r"i\s+(?:really\s+)?enjoy\s+(?:talking|chatting|speaking)\s+(?:to|with)\s+you",
        # Fillers / backchannels
        r"lol",
        r"haha",
        r"hehe",
        r"lmao",
        r"rofl",
        r"\.\.\.",
        r"hmm+",
        r"uh+",
        r"um+",
        r"err+",
        r"ah+",
        r"oh+",
        r"ok(?:ay)?",
        r"sure",
        r"yep",
        r"yup",
        r"nope",
        r"nah",
        r"yes\s+please",
        r"no\s+thanks",
        r"cool",
        r"awesome",
        r"great",
        r"nice",
        r"wow",
        r"interesting",
        r"i\s+see",
        r"got\s+it",
        r"understood",
        # Follow-ups / clarification
        r"translate\s*:\s*.+",  # "Translate: La vie est belle" → TranslateTool
        r"can\s+you\s+(?:explain|elaborate|clarify|simplify|rephrase|repeat)(?:\s+that)?",
        r"i\s+(?:did\s+not|didn.t|don.t)\s+(?:understand|get\s+it|follow)",
        r"what\s+do\s+you\s+mean",
        r"could\s+you\s+(?:say\s+that\s+again|repeat\s+that|be\s+more\s+specific)",
        r"please\s+(?:simplify|explain|elaborate|continue|go\s+on)",
    ],
    Lang.FRENCH: [
        r"bonjour",
        r"bonsoir",
        r"salut",
        r"merci",
        r"au\s+revoir",
        r"bonne\s+nuit",
        r"bonne\s+journée",
        r"enchanté",
    ],
    Lang.GERMAN: [
        r"hallo",
        r"guten\s+(?:morgen|abend|tag|nacht)",
        r"danke",
        r"tschüss",
        r"auf\s+wiedersehen",
        r"wie\s+geht.s",
    ],
    Lang.SPANISH: [
        r"hola",
        r"buenos\s+(?:días|tardes|noches)",
        r"gracias",
        r"adiós",
        r"buenas",
        r"de\s+nada",
    ],
    Lang.PORTUGUESE: [
        r"olá",
        r"bom\s+(?:dia|tarde|noite)",
        r"obrigad[oa]",
        r"tchau",
        r"adeus",
        r"oi",
    ],
    Lang.ITALIAN: [
        r"buongiorno",
        r"buonasera",
        r"buonanotte",
        r"grazie",
        r"arrivederci",
        r"prego",
    ],
    Lang.DUTCH: [
        r"hallo",
        r"goedemorgen",
        r"goedemiddag",
        r"goedenavond",
        r"dankjewel",
        r"bedankt",
        r"tot\s+ziens",
    ],
    Lang.SWEDISH: [
        r"hej",
        r"god\s+(?:morgon|kväll|natt)",
        r"tack",
        r"hejdå",
        r"adjö",
    ],
    Lang.NORWEGIAN: [
        r"hei",
        r"god\s+(?:morgen|kveld|natt)",
        r"takk",
        r"ha\s+det",
    ],
    Lang.DANISH: [
        r"hej",
        r"god\s+(?:morgen|aften|nat)",
        r"tak",
        r"farvel",
    ],
    Lang.FINNISH: [
        r"hei",
        r"hyvää\s+(?:huomenta|iltaa|yötä)",
        r"kiitos",
        r"näkemiin",
    ],
    Lang.POLISH: [
        r"cześć",
        r"dzień\s+dobry",
        r"dobry\s+wieczór",
        r"dziękuję",
        r"do\s+widzenia",
    ],
    Lang.TURKISH: [
        r"merhaba",
        r"günaydın",
        r"iyi\s+(?:günler|akşamlar|geceler)",
        r"teşekkür\s+ederim",
        r"hoşça\s+kal",
    ],
    Lang.INDONESIAN: [
        r"halo",
        r"selamat\s+(?:pagi|siang|malam)",
        r"terima\s+kasih",
        r"sampai\s+jumpa",
        r"apa\s+kabar",
    ],
    Lang.RUSSIAN: [
        r"привет",
        r"здравствуй",
        r"спасибо",
        r"до\s+свидания",
        r"добрый\s+(?:день|вечер|утро)",
        r"пока",
    ],
    Lang.KOREAN: [
        r"안녕",
        r"감사",
        r"고마워",
        r"잘\s*가",
        r"안녕히",
        r"반가워",
        r"좋은\s*아침",
        r"좋은\s*저녁",
        r"잘\s*자",
        r"사랑해",
    ],
    Lang.JAPANESE: [
        r"こんにちは",
        r"こんばんは",
        r"おはよう",
        r"おやすみ",
        r"ありがとう",
        r"さようなら",
        r"またね",
        r"よろしく",
        r"大好き",
        r"愛してる",
    ],
    Lang.CHINESE: [
        r"你好",
        r"晚上好",
        r"早上好",
        r"谢谢",
        r"再见",
        r"再會",
        r"不客气",
    ],
    Lang.ARABIC: [
        r"مرحبا",
        r"السلام",
        r"شكرا",
        r"وداعا",
        r"مساء\s+الخير",
        r"صباح\s+الخير",
    ],
    Lang.HINDI: [
        r"नमस्ते",
        r"धन्यवाद",
        r"अलविदा",
        r"सुप्रभात",
    ],
    Lang.GREEK: [
        r"γεια",
        r"καλημέρα",
        r"καλησπέρα",
        r"ευχαριστώ",
        r"αντίο",
    ],
    Lang.HEBREW: [
        r"שלום",
        r"תודה",
        r"להתראות",
        r"בוקר\s+טוב",
    ],
    Lang.THAI: [
        r"สวัสดี",
        r"ขอบคุณ",
        r"ลาก่อน",
    ],
    Lang.VIETNAMESE: [
        r"xin\s+chào",
        r"cảm\s+ơn",
        r"tạm\s+biệt",
        r"chào",
    ],
}


# ---------------------------------------------------------------------------
# Lookup maps built once at import time
# ---------------------------------------------------------------------------

_NAME_TO_LANG: Dict[str, Lang] = {lang.name.lower(): lang for lang in Lang}
_CODE_TO_LANG: Dict[str, Lang] = {lang.value: lang for lang in Lang}

# Convenience dicts for callers that need raw strings
LANG_NAME_TO_CODE: Dict[str, str] = {lang.name.lower(): lang.code for lang in Lang}
LANG_CODE_TO_NAME: Dict[str, str] = {lang.code: lang.label for lang in Lang}


# ---------------------------------------------------------------------------
# Script-based language detection
# ---------------------------------------------------------------------------


def detect_lang(text: str) -> Optional[Lang]:
    """Detect the dominant non-Latin script language in text.

    Scans the first 200 chars and returns the Lang whose script appears most.
    Returns None if only ASCII/Latin characters are present.

    Examples::

        detect_lang("안녕하세요")  ->  Lang.KOREAN
        detect_lang("こんにちは")  ->  Lang.JAPANESE
        detect_lang("Hello")      ->  None
    """
    sample = text[:200]
    counts: Dict[str, int] = {}
    for ch in sample:
        for start, end, code in _SCRIPT_RANGES:
            if start <= ch <= end:
                counts[code] = counts.get(code, 0) + 1
                break
    if not counts:
        return None
    dominant_code = max(counts, key=lambda c: counts[c])
    return Lang.from_code(dominant_code)


# ---------------------------------------------------------------------------
# Social-phrase pattern — compiled from Lang.social_phrases at import time.
# Matches short conversational prompts (greetings, thanks, farewells, etc.)
# so the inference layer can route them to the smalltalk category.
# ---------------------------------------------------------------------------


def _build_social_pattern() -> "Pattern[str]":
    """Build SOCIAL_PATTERN from every Lang's social_phrases list.

    Matches prompts that:
    - Consist entirely of social phrases (e.g. "Hello", "Goodbye!")
    - Start with a social phrase (e.g. "Hello there!", "Good evening, how are you?")
    - Are a direct social question (e.g. "How are you doing today?")
    """
    parts: List[str] = []
    for lang in Lang:
        for phrase in lang.social_phrases:
            if all(ord(c) < 128 for c in phrase.replace(r"\s", " ").replace(r"\S", " ")):
                parts.append(r"\b" + phrase + r"\b")
            else:
                parts.append(phrase)
    alternation = "|".join(parts)
    unit = r"(?:" + alternation + r")"
    return re.compile(
        r"^\s*" + unit + r"(?:[!?,.\s]*\S*)*\s*$",
        re.IGNORECASE,
    )


SOCIAL_PATTERN: "Pattern[str]" = _build_social_pattern()


# ---------------------------------------------------------------------------
# Offline translation pack configuration
# ---------------------------------------------------------------------------

# Languages with argostranslate packs — all i→j pairs are attempted by
# `tinytot-ingest translate-packs`. Extend this list to add more languages.
TRANSLATE_LANGS: List[Lang] = [
    Lang.ENGLISH,
    Lang.FRENCH,
    Lang.GERMAN,
    Lang.SPANISH,
    Lang.KOREAN,
    Lang.CHINESE,
    Lang.JAPANESE,
    Lang.PORTUGUESE,
    Lang.ITALIAN,
    Lang.ARABIC,
    Lang.HINDI,
    Lang.RUSSIAN,
]

# All pairwise combinations where source != target
TRANSLATE_PAIRS: List[Tuple[str, str]] = [
    (src.code, tgt.code) for src in TRANSLATE_LANGS for tgt in TRANSLATE_LANGS if src is not tgt
]

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

# Pipe-separated language names for use in re.compile() patterns
LANG_NAMES_PATTERN: str = "|".join(sorted(_NAME_TO_LANG.keys()))

"""GDELT's language names to the codes Wikidata labels are keyed by.

Two systems name languages differently and neither is going to change, so the mapping
is explicit and the gap between them is a first-class value: a language this table does
not know is **unmappable**, and a row in it can only ever be *not evaluable*. That is
the fail-safe direction. The alternative — guessing, or falling back to script — is the
defect #49 records, where a Bulgarian headline was measured against Russian aliases and
its author was recorded as having omitted an actor they had in fact named.

GDELT's own casing is inconsist: `ENGLISH` and `SPANISH` shout, `Chinese`, `ChineseT`
and `Korean` do not. Lookup folds case, so the table is written once in the shape GDELT
sends and matched however it arrives.
"""

# GDELT name -> the language code Wikidata keys labels and aliases by.
_CODES = {
    "albanian": "sq",
    "arabic": "ar",
    "armenian": "hy",
    "azerbaijani": "az",
    "bengali": "bn",
    "bosnian": "bs",
    "bulgarian": "bg",
    "burmese": "my",
    "catalan": "ca",
    "chinese": "zh",
    # Traditional Chinese is a separate label set on Wikidata, not a variant of `zh`.
    "chineset": "zh-hant",
    "croatian": "hr",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "english": "en",
    "estonian": "et",
    "finnish": "fi",
    "french": "fr",
    "georgian": "ka",
    "german": "de",
    "greek": "el",
    "gujarati": "gu",
    "hebrew": "he",
    "hindi": "hi",
    "hungarian": "hu",
    "icelandic": "is",
    "indonesian": "id",
    "italian": "it",
    "japanese": "ja",
    "kannada": "kn",
    "kazakh": "kk",
    "korean": "ko",
    "latvian": "lv",
    "lithuanian": "lt",
    "macedonian": "mk",
    "malay": "ms",
    "malayalam": "ml",
    "marathi": "mr",
    "mongolian": "mn",
    # Wikidata labels Norwegian as bokmål; `no` exists but is sparser.
    "norwegian": "nb",
    "persian": "fa",
    "polish": "pl",
    "portuguese": "pt",
    "punjabi": "pa",
    "romanian": "ro",
    "russian": "ru",
    "serbian": "sr",
    "sinhala": "si",
    "slovak": "sk",
    "slovenian": "sl",
    "somali": "so",
    "spanish": "es",
    "swahili": "sw",
    "swedish": "sv",
    "tamil": "ta",
    "telugu": "te",
    "thai": "th",
    "turkish": "tr",
    "ukrainian": "uk",
    "urdu": "ur",
    "uzbek": "uz",
    "vietnamese": "vi",
}


def code_for(name: str | None) -> str | None:
    """The Wikidata language code for a GDELT language name, or None if unmapped.

    None is a real answer, not a failure: it means no alias in that language was ever
    fetched, so nothing can be concluded about a headline written in it.
    """
    if not name:
        return None
    return _CODES.get(name.strip().casefold())


def codes() -> list[str]:
    """Every language this project can read, for the alias builder to fetch."""
    return sorted(set(_CODES.values()))


def names() -> list[str]:
    """The GDELT spellings, for tests and for auditing coverage against a window."""
    return sorted(_CODES)

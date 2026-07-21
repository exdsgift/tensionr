"""NER keyword extraction (spaCy multilingual model, lazily loaded)."""

import logging
from collections import Counter
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _nlp():
    import spacy

    return spacy.load("xx_ent_wiki_sm")


def extract_keywords(articles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    entities: list[tuple[str, str]] = []
    nlp = _nlp()
    for art in articles:
        text = art.get("title", "")
        if not text:
            continue
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("GPE", "ORG", "NORP", "PERSON", "LOC", "PER"):
                clean = ent.text.strip().lower()
                if len(clean) > 2:
                    entities.append((clean, ent.label_))

    counts = Counter(entities)
    return {
        name: {"count": count, "type": label}
        for (name, label), count in counts.most_common(60)
    }

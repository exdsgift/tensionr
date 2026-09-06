"""Alias selection, the audit row, and loading the table from data."""

import json

from tensionr.stories.wikidata import (
    describe,
    language_scripts,
    load,
    read_seeds,
    select_aliases,
    write,
)

ENTITY = {
    "id": "Q794",
    "labels": {
        "en": {"value": "Iran"},
        "ar": {"value": "إيران"},
        "el": {"value": "Ιράν"},
        "ru": {"value": "Иран"},
    },
    "aliases": {
        "en": [{"value": "Islamic Republic of Iran"}, {"value": "IR"}],
        "ar": [{"value": "الجمهورية الإسلامية الإيرانية"}],
    },
    "descriptions": {"en": {"value": "country in West Asia"}},
    "claims": {
        "P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q6256"}}}}],
    },
}


def test_labels_and_aliases_are_kept_under_the_language_they_came_from():
    """Keyed by language, because language is what decides evaluability (#49)."""
    aliases = select_aliases(ENTITY)
    assert aliases["en"] == ["Iran", "Islamic Republic of Iran"]
    assert aliases["ar"] == ["إيران", "الجمهورية الإسلامية الإيرانية"]
    assert aliases["el"] == ["Ιράν"]
    assert aliases["ru"] == ["Иран"]


def test_a_language_with_nothing_usable_is_absent_rather_than_empty():
    """An empty list would read as "we can read this language", which is the defect."""
    entity = {"labels": {"en": {"value": "Iran"}, "de": {"value": "IR"}}, "aliases": {}}
    assert "de" not in select_aliases(entity)


def test_the_same_string_is_kept_in_every_language_that_uses_it():
    """ "Iran" in English and Italian are two separate claims about what can be read."""
    entity = {
        "labels": {"en": {"value": "Iran"}, "it": {"value": "Iran"}},
        "aliases": {},
    }
    assert select_aliases(entity) == {"en": ["Iran"], "it": ["Iran"]}


def test_unusable_aliases_are_filtered_at_build_time_not_match_time():
    # "IR" is a two-letter Latin string and would match half the corpus.
    assert "IR" not in select_aliases(ENTITY)["en"]


def test_duplicates_are_dropped_case_insensitively():
    entity = {
        "labels": {"en": {"value": "Iran"}},
        "aliases": {"en": [{"value": "IRAN"}]},
    }
    assert select_aliases(entity) == {"en": ["Iran"]}


def test_languages_outside_the_list_are_ignored():
    entity = {"labels": {"vo": {"value": "Iranän"}}, "aliases": {}}
    assert select_aliases(entity, ["en"]) == {}


def test_an_entity_with_nothing_usable_yields_nothing():
    assert select_aliases({"labels": {}, "aliases": {}}) == {}


def test_the_audit_row_carries_what_a_human_needs_to_check_the_pick():
    row = describe(ENTITY)
    assert row == {
        "qid": "Q794",
        "label": "Iran",
        "description": "country in West Asia",
        "instance_of": ["Q6256"],
    }


def test_the_table_round_trips_through_data(tmp_path):
    path = tmp_path / "aliases.json"
    payload = {
        "table": {"iran": {"en": ["Iran"], "ar": ["إيران"]}},
        "audit": [],
        "missing": [],
    }
    write(payload, path)
    assert json.loads(path.read_text("utf-8"))["table"]["iran"]["ar"] == ["إيران"]

    table = load(path)
    assert table.actors() == ["iran"]
    assert table.scripts_for("iran") == {"latin", "arabic"}
    assert table.languages_for("iran") == {"en", "ar"}


def test_seeds_are_read_from_data_with_their_audit_fields(tmp_path):
    path = tmp_path / "seeds.json"
    path.write_text(
        json.dumps(
            {
                "_comment": "not an actor",
                "actors": {
                    "iran": {"qid": "Q794", "label": "Iran", "description": "country"}
                },
            }
        ),
        "utf-8",
    )
    assert read_seeds(path) == {"iran": "Q794"}


class TestTheMulLabelAndTheFamilyName:
    """Wikidata moved shared names to `mul`, and headlines write surnames.

    Q22686 is fully migrated: it carries `mul: "Donald Trump"` and Cyrillic, Chinese
    and Hebrew labels, and no English, Spanish, Italian or French label at all. Reading
    only per-language labels produced a table where Trump had no Latin alias, so every
    English headline came back `unresolved` rather than measured. Of 248 Latin-script
    headlines containing the word Trump, the engine named him in none.

    The two halves have to land together. `mul` alone restores evaluability without
    restoring matching, and measured on the same 248 headlines that turns 213 honest
    "cannot be answered" into 238 rows claiming Trump was not named by headlines whose
    first word is Trump. That is #49's failure, manufactured. With the family name from
    P734 beside it: 248 of 248, and 125 of 125 for Putin.
    """

    ENTITY = {
        "labels": {
            "mul": {"value": "Donald Trump"},
            "ru": {"value": "Дональд Трамп"},
        },
        "aliases": {},
    }
    SCRIPTS = {"en": "latin", "es": "latin", "ru": "cyrillic", "ja": "cjk"}

    def test_mul_fills_in_for_a_language_with_no_label_of_its_own(self):
        picked = select_aliases(
            self.ENTITY, languages=["en", "es"], scripts=self.SCRIPTS
        )
        assert picked == {"en": ["Donald Trump"], "es": ["Donald Trump"]}

    def test_a_language_with_its_own_label_keeps_it(self):
        picked = select_aliases(self.ENTITY, languages=["ru"], scripts=self.SCRIPTS)
        assert picked == {"ru": ["Дональд Трамп"]}

    def test_mul_is_refused_where_the_script_does_not_match(self):
        # #49: claiming a row is answerable when it is not manufactures false
        # omissions. A Japanese headline will not carry "Donald Trump" in Latin.
        assert select_aliases(self.ENTITY, languages=["ja"], scripts=self.SCRIPTS) == {}

    def test_and_where_the_script_of_the_language_is_simply_unknown(self):
        assert select_aliases(self.ENTITY, languages=["en"], scripts={}) == {}

    def test_the_script_of_a_language_is_counted_from_the_labels(self):
        scripts = language_scripts(
            {
                "Q1": {
                    "labels": {
                        "en": {"value": "Donald Trump"},
                        "ru": {"value": "Дональд Трамп"},
                    }
                },
                "Q2": {
                    "labels": {
                        "en": {"value": "Vladimir Putin"},
                        "ru": {"value": "Владимир Путин"},
                    }
                },
            }
        )
        assert scripts == {"en": "latin", "ru": "cyrillic"}

    def test_mul_itself_never_becomes_a_language(self):
        # It is a statement about other languages, not a language a headline is in.
        assert "mul" not in language_scripts(
            {"Q1": {"labels": {"mul": {"value": "Trump"}}}}
        )

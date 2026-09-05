"""Alias selection, the audit row, and loading the table from data."""

import json

from tensionr.stories.wikidata import describe, load, read_seeds, select_aliases, write

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

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


def test_labels_and_aliases_are_taken_across_languages():
    aliases = select_aliases(ENTITY)
    assert "Iran" in aliases
    assert "إيران" in aliases
    assert "Ιράν" in aliases
    assert "Islamic Republic of Iran" in aliases


def test_unusable_aliases_are_filtered_at_build_time_not_match_time():
    # "IR" is a two-letter Latin string and would match half the corpus.
    assert "IR" not in select_aliases(ENTITY)


def test_duplicates_are_dropped_case_insensitively():
    entity = {
        "labels": {"en": {"value": "Iran"}},
        "aliases": {"en": [{"value": "IRAN"}]},
    }
    assert select_aliases(entity) == ["Iran"]


def test_languages_outside_the_list_are_ignored():
    entity = {"labels": {"vo": {"value": "Iranän"}}, "aliases": {}}
    assert select_aliases(entity, ["en"]) == []


def test_an_entity_with_nothing_usable_yields_nothing():
    assert select_aliases({"labels": {}, "aliases": {}}) == []


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
    write({"table": {"iran": ["Iran", "إيران"]}, "audit": [], "missing": []}, path)
    assert json.loads(path.read_text("utf-8"))["table"]["iran"] == ["Iran", "إيران"]

    table = load(path)
    assert table.actors() == ["iran"]
    assert table.scripts_for("iran") == {"latin", "arabic"}


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

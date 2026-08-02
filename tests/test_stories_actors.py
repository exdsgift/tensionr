"""Alias usability, script detection, and the three-state resolve across scripts."""

import pytest

from tensionr.stories.actors import AliasTable, coverage, script_of, usable_alias
from tensionr.stories.measure import ABSENT, PRESENT, UNRESOLVED

TABLE = {
    "iran": ["Iran", "Irán", "إيران", "Ιράν", "Иран"],
    "trump": ["Trump", "ترامب"],
    "hormuz": ["Strait of Hormuz", "Hormuz", "هرمز"],
    "china": ["China", "中国"],
}


@pytest.fixture
def table():
    return AliasTable(TABLE)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Trump halts Iran strikes", "latin"),
        ("إيران ترد على ترامب", "arabic"),
        ("Το Ιράν διαψεύδει", "greek"),
        ("Иран ответил Трампу", "cyrillic"),
        ("中国外交部回应", "cjk"),
        ("2026", "other"),
    ],
)
def test_script_detection(text, expected):
    assert script_of(text) == expected


def test_the_length_floor_is_per_script_not_global():
    # Two Latin characters are noise; two CJK characters are a word. A single global
    # floor deleted every CJK alias in an earlier build.
    assert usable_alias("US") is False
    assert usable_alias("中国") is True
    assert usable_alias("هرمز") is True


def test_the_code_shape_filter_is_ascii_only():
    # Applied to other scripts this rejects ordinary words, silently emptying them.
    assert usable_alias("ISO-3166") is False
    assert usable_alias("Q794") is False
    assert usable_alias("إيران") is True
    assert usable_alias("Иран") is True


def test_unusable_aliases_are_dropped_visibly():
    built = AliasTable({"iran": ["Iran", "IR", "Q794"]})
    assert [a for _, a in built.dropped] == ["IR", "Q794"]
    assert built.scripts_for("iran") == {"latin"}


def test_present_and_absent_in_latin(table):
    assert table.resolve("Trump halts Iran strikes", "iran") == PRESENT
    assert table.resolve("Trump halts strikes", "iran") == ABSENT


def test_accents_do_not_hide_a_match(table):
    assert table.resolve("Trump suspende ataques contra Irán", "iran") == PRESENT


def test_a_longer_alias_still_matches_inside_a_headline(table):
    assert table.resolve("Iran rejects Strait of Hormuz deal", "hormuz") == PRESENT


def test_an_actor_with_no_alias_in_the_title_script_is_undecidable(table):
    # The table has no Greek alias for Trump, so a Greek headline cannot be answered.
    assert table.resolve("Ο Τραμπ ανακοίνωσε", "trump") == UNRESOLVED
    # but Iran has one, so the same headline is answerable for Iran
    assert table.resolve("Το Ιράν διαψεύδει", "iran") == PRESENT


def test_arabic_matches_without_word_boundaries(table):
    assert table.resolve("إيران ترد على ترامب", "iran") == PRESENT
    assert table.resolve("إيران ترد على ترامب", "trump") == PRESENT
    assert table.resolve("إيران ترد", "trump") == ABSENT


def test_cjk_matches_without_spaces(table):
    assert table.resolve("中国外交部回应美国制裁", "china") == PRESENT


def test_an_unknown_actor_is_undecidable_rather_than_absent(table):
    assert table.resolve("Trump halts Iran strikes", "not-in-table") == UNRESOLVED


def test_coverage_separates_answerable_from_named(table):
    rows = [
        {"title": "Trump halts Iran strikes"},
        {"title": "Trump halts strikes"},
        {"title": "Ο Τραμπ ανακοίνωσε"},
    ]
    seen = coverage(table, rows, "trump")
    assert seen["latin"] == {"rows": 2, "answerable": 2, "named": 2}
    # answerable but never matched is the morphology hazard; here it is simply
    # unanswerable, and the two must not be conflated
    assert seen["greek"] == {"rows": 1, "answerable": 0, "named": 0}

"""Alias usability, script detection, and the three-state resolve across scripts."""

import pytest

from tensionr.stories.actors import AliasTable, coverage, script_of, usable_alias
from tensionr.stories.marks import ABSENT, PRESENT, UNRESOLVED

# Keyed by language, because that is what decides whether a row can be answered at all
# (#49). The scripts follow from the strings.
TABLE = {
    "iran": {
        "en": ["Iran"],
        "es": ["Irán"],
        "ar": ["إيران"],
        "el": ["Ιράν"],
        "ru": ["Иран"],
    },
    "trump": {"en": ["Trump"], "ar": ["ترامب"]},
    "hormuz": {"en": ["Strait of Hormuz", "Hormuz"], "ar": ["هرمز"]},
    "china": {"en": ["China"], "zh": ["中国"]},
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
    built = AliasTable({"iran": {"en": ["Iran", "IR", "Q794"]}})
    assert [a for _, a in built.dropped] == ["IR", "Q794"]
    assert built.scripts_for("iran") == {"latin"}


def test_present_and_absent_in_latin(table):
    assert table.resolve("Trump halts Iran strikes", "iran", "ENGLISH") == PRESENT
    assert table.resolve("Trump halts strikes", "iran", "ENGLISH") == ABSENT


def test_accents_do_not_hide_a_match(table):
    assert (
        table.resolve("Trump suspende ataques contra Irán", "iran", "SPANISH")
        == PRESENT
    )


def test_a_longer_alias_still_matches_inside_a_headline(table):
    assert (
        table.resolve("Iran rejects Strait of Hormuz deal", "hormuz", "ENGLISH")
        == PRESENT
    )


def test_an_actor_with_no_alias_in_the_title_script_is_undecidable(table):
    # The table has no Greek alias for Trump, so a Greek headline cannot be answered.
    assert table.resolve("Ο Τραμπ ανακοίνωσε", "trump", "GREEK") == UNRESOLVED
    # but Iran has one, so the same headline is answerable for Iran
    assert table.resolve("Το Ιράν διαψεύδει", "iran", "GREEK") == PRESENT


def test_arabic_matches_without_word_boundaries(table):
    assert table.resolve("إيران ترد على ترامب", "iran", "ARABIC") == PRESENT
    assert table.resolve("إيران ترد على ترامب", "trump", "ARABIC") == PRESENT
    assert table.resolve("إيران ترد", "trump", "ARABIC") == ABSENT


def test_cjk_matches_without_spaces(table):
    assert table.resolve("中国外交部回应美国制裁", "china", "Chinese") == PRESENT


def test_an_unknown_actor_is_undecidable_rather_than_absent(table):
    assert (
        table.resolve("Trump halts Iran strikes", "not-in-table", "ENGLISH")
        == UNRESOLVED
    )


def test_coverage_separates_answerable_from_named(table):
    rows = [
        {"title": "Trump halts Iran strikes", "language": "ENGLISH"},
        {"title": "Trump halts strikes", "language": "ENGLISH"},
        {"title": "Ο Τραμπ ανακοίνωσε", "language": "GREEK"},
    ]
    seen = coverage(table, rows, "trump")
    assert seen["latin"] == {"rows": 2, "answerable": 2, "named": 2}
    # answerable but never matched is the morphology hazard; here it is simply
    # unanswerable, and the two must not be conflated
    assert seen["greek"] == {"rows": 1, "answerable": 0, "named": 0}


def test_a_language_the_table_was_never_built_for_is_undecidable(table):
    """The #49 defect, as a test.

    A Bulgarian headline naming Russia in Bulgarian must not be recorded as an omission
    just because Cyrillic aliases exist for Russian. Here `iran` has a Russian alias and
    no Bulgarian one, and the Bulgarian row is unanswerable rather than absent.
    """
    assert table.resolve("Иран отговори", "iran", "RUSSIAN") == PRESENT
    assert table.resolve("Иран отговори", "iran", "BULGARIAN") == UNRESOLVED


def test_a_language_nobody_mapped_is_undecidable(table):
    assert table.resolve("Trump halts Iran strikes", "iran", "KLINGON") == UNRESOLVED
    assert table.resolve("Trump halts Iran strikes", "iran", None) == UNRESOLVED


def test_matching_still_uses_every_alias_in_the_script(table):
    """Evaluability is per language; matching is per script, and deliberately wider.

    A Spanish page carrying the English spelling is still a naming. More aliases can
    turn absent into present but can never manufacture an omission, and omission is the
    signal.
    """
    assert table.resolve("El presidente de Iran responde", "iran", "SPANISH") == PRESENT


def test_the_pre_49_flat_table_is_refused_rather_than_loaded():
    with pytest.raises(ValueError, match="keyed by language"):
        AliasTable({"iran": ["Iran", "Irán"]})


def test_languages_for_reports_what_an_actor_can_be_read_in(table):
    assert table.languages_for("trump") == {"en", "ar"}
    assert table.languages_for("not-in-table") == set()


def test_the_title_memo_cannot_leak_between_rows():
    """`resolve` caches the title's script and folded form across the actor loop.

    The loop asks about one headline for every actor in turn, so the cache is there to
    stop thirteen of fourteen calls redoing the same NFKD pass. It is keyed by the
    title, and this is what would catch it if it ever stopped being: the answers to an
    interleaved sequence must match the answers to the same calls made in isolation.
    """
    spec = {
        "iran": {"en": ["Iran", "Tehran"]},
        "trump": {"en": ["Trump", "Donald Trump"]},
    }
    table = AliasTable(spec)
    titles = [
        "Iran responds to Washington",
        "Trump halts the strikes",
        "Tehran and Trump trade blame",
        "A story about neither",
    ]
    alone = {
        (t, a): AliasTable(spec).resolve(t, a, "ENGLISH")
        for t in titles
        for a in ("iran", "trump")
    }
    interleaved = {
        (t, a): table.resolve(t, a, "ENGLISH")
        for t in titles
        for a in ("iran", "trump")
    }
    assert interleaved == alone
    assert alone[(titles[2], "iran")] == PRESENT
    assert alone[(titles[3], "trump")] == ABSENT

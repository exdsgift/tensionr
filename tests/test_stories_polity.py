"""Domain to polity, and the refusal to guess."""

import json

from tensionr.stories.polity import PolityTable


def table():
    return PolityTable(
        {"aljazeera.com": "Qatar", "presstv.co.uk": "Iran"},
        {"fr": "France", "co.uk": "United Kingdom"},
    )


def test_an_explicit_entry_beats_the_tld():
    # Press TV publishes on a .co.uk domain and is Iranian.
    assert table().of("presstv.co.uk") == "Iran"
    assert table().of("bbc.co.uk") == "United Kingdom"


def test_a_generic_tld_is_unplaced_rather_than_guessed():
    # Guessing would put every .com in one bucket and invent agreement between
    # unrelated outlets, which is the opposite of what the axis is for.
    assert table().of("somewhere.com") is None


def test_www_and_case_do_not_matter():
    assert table().of("WWW.LeMonde.FR") == "France"


def test_coverage_reports_how_much_can_be_placed():
    assert table().coverage(["lemonde.fr", "x.com", "aljazeera.com"]) == {
        "domains": 3,
        "placed": 2,
        "rate": 0.6667,
    }


def test_coverage_of_nothing_is_zero_not_an_error():
    assert table().coverage([])["rate"] == 0.0


def test_it_loads_from_data(tmp_path):
    path = tmp_path / "domains.json"
    path.write_text(
        json.dumps({"domains": {"a.test": "Spain"}, "tlds": {"it": "Italy"}}), "utf-8"
    )
    loaded = PolityTable.load(path)
    assert loaded.of("a.test") == "Spain"
    assert loaded.of("b.it") == "Italy"

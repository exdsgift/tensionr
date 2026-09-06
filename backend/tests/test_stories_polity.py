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


class TestTheBulkLookupIsOnlyEverAdditive:
    """It answers where the hand table and the TLDs are silent, and nowhere else.

    That order is the whole safety argument. GDELT's table calls `aljazeera.com`
    United States, `aljazeera.net` Israel and `reuters.com` United States, and this
    repository has hand-written entries that say otherwise. Measured on a real window
    the two agree on 95.2% of the domains both can answer, but the 4.8% they do not
    is concentrated in exactly the outlets somebody already found worth correcting,
    so the hand table has to win every time it has an opinion.
    """

    TABLE = {"aljazeera.com": "Qatar"}
    TLDS = {"fr": "France"}
    BULK = {
        "aljazeera.com": "United States",
        "lemonde.fr": "Belgium",
        "example.com": "Japan",
        "news.example.com": "Japan",
    }

    def table(self) -> PolityTable:
        return PolityTable(self.TABLE, self.TLDS, self.BULK)

    def test_a_hand_written_entry_is_never_overruled(self):
        assert self.table().of("aljazeera.com") == "Qatar"

    def test_and_neither_is_the_tld(self):
        assert self.table().of("lemonde.fr") == "France"

    def test_it_answers_where_both_are_silent(self):
        assert self.table().of("example.com") == "Japan"

    def test_a_subdomain_falls_back_to_its_parent(self):
        # GDELT's own coverage went from 94.1% to 98.7% on this alone.
        assert (
            PolityTable({}, {}, {"example.com": "Japan"}).of("blog.example.com")
            == "Japan"
        )

    def test_a_domain_nobody_knows_is_still_unplaced(self):
        assert self.table().of("nowhere.example") is None

    def test_www_is_stripped_before_the_lookup(self):
        assert self.table().of("www.example.com") == "Japan"

    def test_a_checkout_without_the_bulk_file_still_places_what_it_can(self):
        # The file is a build artefact of tools/build_polity_lookup.py. Its absence
        # must cost coverage, never correctness.
        bare = PolityTable(self.TABLE, self.TLDS)
        assert bare.of("aljazeera.com") == "Qatar"
        assert bare.of("lemonde.fr") == "France"
        assert bare.of("example.com") is None

"""Whether the naming split aligns with the polity, and when the question cannot be asked.

The test that matters is the first one: a split that is perfectly even, which `division`
scores 1.00 and puts at the top of the ledger, must come out indistinguishable from
chance when the countries are irrelevant to it. That is the whole reason this module
exists.
"""

from tensionr.stories.structure import structure

ROUNDS = 400  # enough to separate 0.5 from 0.005; the shipped default is 2000


def rows(spec: list[tuple[str, int]], actor: str = "x") -> list[dict]:
    """`spec` is (polity, named) per source."""
    return [
        {
            "domain": f"d{i}.test",
            "polity": polity,
            "marks": {actor: "present" if named else "absent"},
        }
        for i, (polity, named) in enumerate(spec)
    ]


class TestAnEvenSplitIsNotAFinding:
    def test_a_coin_flip_across_countries_is_indistinguishable_from_chance(self):
        # Six countries, each internally half and half. Division would be 1.00, the
        # maximum, and the ledger would rank it first. Knowing the country tells you
        # nothing.
        spec = []
        for country in ("A", "B", "C", "D", "E", "F"):
            spec += [(country, 1), (country, 0), (country, 1), (country, 0)]
        result = structure(rows(spec), "x", rounds=ROUNDS)
        assert result is not None
        assert result["p"] > 0.2, result

    def test_the_same_split_arranged_by_country_is(self):
        # The same 12 named and 12 not, and the same six countries. Only the
        # correspondence changes.
        spec = []
        for country in ("A", "B", "C"):
            spec += [(country, 1)] * 4
        for country in ("D", "E", "F"):
            spec += [(country, 0)] * 4
        result = structure(rows(spec), "x", rounds=ROUNDS)
        assert result is not None
        assert result["p"] <= 0.01, result


class TestWhenTheQuestionCannotBeAsked:
    def test_one_polity_cannot_disagree_with_anything(self):
        assert structure(rows([("A", 1), ("A", 0), ("A", 1), ("A", 0)]), "x") is None

    def test_a_unanimous_story_has_no_split_to_be_structured(self):
        spec = [("A", 1), ("B", 1), ("C", 1), ("D", 1)]
        assert structure(rows(spec), "x", rounds=ROUNDS) is None

    def test_a_story_nobody_named_is_the_same(self):
        spec = [("A", 0), ("B", 0), ("C", 0), ("D", 0)]
        assert structure(rows(spec), "x", rounds=ROUNDS) is None

    def test_rows_with_no_polity_cannot_speak_to_a_question_about_polities(self):
        spec = [("A", 1), ("A", 1), ("B", 0), ("B", 0)]
        with_nulls = (
            rows(spec)
            + [{"domain": "n.test", "polity": None, "marks": {"x": "present"}}] * 6
        )
        result = structure(with_nulls, "x", rounds=ROUNDS)
        assert result is not None
        assert result["sources"] == 4

    def test_an_unresolved_mark_carries_no_evidence_either_way(self):
        spec = [("A", 1), ("A", 1), ("B", 0), ("B", 0)]
        with_unresolved = (
            rows(spec)
            + [{"domain": "u.test", "polity": "C", "marks": {"x": "unresolved"}}] * 4
        )
        result = structure(with_unresolved, "x", rounds=ROUNDS)
        assert result is not None
        # The four unresolved rows are excluded, so C never enters the table.
        assert result["sources"] == 4
        assert {r["polity"] for r in result["by_polity"]} == {"A", "B"}


class TestWhatIsPublished:
    def test_p_is_never_zero_because_a_permutation_test_cannot_prove_it(self):
        spec = [(c, 1) for c in "ABCDEFGH"] + [(c, 0) for c in "IJKLMNOP"]
        result = structure(rows(spec), "x", rounds=ROUNDS)
        assert result["p"] >= result["floor"] > 0

    def test_the_table_counts_what_the_evidence_shows(self):
        spec = [("A", 1), ("A", 1), ("A", 0), ("B", 0), ("B", 0), ("C", 1)]
        result = structure(rows(spec), "x", rounds=ROUNDS)
        table = {r["polity"]: (r["named"], r["evaluable"]) for r in result["by_polity"]}
        assert table == {"A": (2, 3), "B": (0, 2), "C": (1, 1)}

    def test_a_polity_with_fewer_than_three_sources_is_flagged_not_hidden(self):
        # 1/1 = 100% is noise wearing a percentage. Dropping it would hide part of the
        # sample; printing it unmarked would invite the reader to lean on it.
        spec = [("A", 1), ("A", 1), ("A", 0), ("B", 0), ("B", 0), ("C", 1)]
        result = structure(rows(spec), "x", rounds=ROUNDS)
        thin = {r["polity"] for r in result["by_polity"] if r["thin"]}
        assert thin == {"B", "C"}

    def test_an_underpowered_test_says_so(self):
        # Three countries and twelve sources cannot detect anything but a total split.
        spec = [("A", 1)] * 4 + [("B", 0)] * 4 + [("C", 1)] * 4
        result = structure(rows(spec), "x", rounds=ROUNDS)
        assert result["powered"] is False

    def test_a_well_supplied_test_does_not(self):
        spec = []
        for i, country in enumerate("ABCDEFGHIJ"):
            spec += [(country, 1 if i < 5 else 0)] * 6
        result = structure(rows(spec), "x", rounds=ROUNDS)
        assert result["sources"] == 60
        assert result["polities"] == 10
        assert result["powered"] is True

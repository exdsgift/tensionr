"""Story identity across runs: continuation, birth, merge, split and dormancy."""

from tensionr.stories.identity import reconcile, story_id


def urls(*names: str) -> list[str]:
    return [f"https://example.test/{n}" for n in names]


def ids(result) -> list[str]:
    return [a["id"] for a in result["assignments"]]


def kinds(result) -> list[str]:
    return sorted(e["type"] for e in result["events"])


def test_id_is_stable_and_independent_of_order():
    assert story_id(urls("b", "a", "c")) == story_id(urls("c", "a", "b"))
    assert story_id(urls("a")) != story_id(urls("b"))


def test_a_story_that_grows_keeps_its_id():
    first = reconcile([urls("a", "b", "c")], {})
    sid = ids(first)[0]
    known = {a["id"]: a["urls"] for a in first["assignments"]}

    # the next window carries the same articles plus three more
    second = reconcile([urls("a", "b", "c", "d", "e", "f")], known)
    assert ids(second) == [sid]
    assert kinds(second) == []


def test_an_unrelated_cluster_is_born():
    known = {"s-old": urls("a", "b", "c")}
    result = reconcile([urls("x", "y", "z")], known)
    assert kinds(result) == ["created", "dormant"]
    assert ids(result)[0] != "s-old"


def test_two_stories_merging_are_recorded_not_silently_joined():
    known = {"s-one": urls("a", "b", "c", "d"), "s-two": urls("e", "f", "g")}
    result = reconcile([urls("a", "b", "c", "d", "e", "f", "g")], known)

    assert ids(result) == ["s-one"]  # the larger prior story keeps the series
    merged = [e for e in result["events"] if e["type"] == "merged"]
    assert merged == [{"type": "merged", "into": "s-one", "absorbed": ["s-two"]}]
    assert "dormant" not in kinds(result)  # absorbed is not the same as gone


def test_a_story_splitting_keeps_one_id_and_records_the_other():
    known = {"s-one": urls("a", "b", "c", "d", "e", "f")}
    result = reconcile([urls("a", "b", "c"), urls("d", "e", "f")], known)

    assert "s-one" in ids(result)
    assert len(set(ids(result))) == 2
    split = [e for e in result["events"] if e["type"] == "split"]
    assert len(split) == 1
    assert split[0]["from"] == ["s-one"]
    assert split[0]["to"] in ids(result)
    assert split[0]["to"] != "s-one"


def test_a_story_that_leaves_the_window_goes_dormant_rather_than_vanishing():
    known = {"s-gone": urls("a", "b", "c")}
    result = reconcile([], known)
    assert result["assignments"] == []
    assert result["events"] == [{"type": "dormant", "id": "s-gone"}]


def test_one_id_is_never_given_to_two_clusters():
    known = {story_id(urls("a", "b", "c", "d")): urls("a", "b", "c", "d")}
    result = reconcile([urls("a", "b", "c", "d"), urls("a", "b", "c", "d")], known)
    assert len(set(ids(result))) == 2


def test_a_split_half_holding_the_seed_article_does_not_reuse_the_parent_id():
    # Regression: the id is seeded from the earliest URL, so the half keeping that
    # article re-derived the parent's id and two stories shared one identity. Live
    # data showed it as split events whose target equalled their source.
    parent = story_id(urls("a", "b", "c", "d", "e", "f"))
    known = {parent: urls("a", "b", "c", "d", "e", "f")}
    result = reconcile([urls("d", "e", "f"), urls("a", "b", "c")], known)

    assert len(set(ids(result))) == 2, "both halves were given the same id"
    split = [e for e in result["events"] if e["type"] == "split"]
    assert split and split[0]["to"] != split[0]["from"][0]


def test_slight_overlap_is_not_the_same_story():
    # one shared article out of five is coincidence, not continuation
    known = {"s-one": urls("a", "b", "c", "d", "e")}
    result = reconcile([urls("a", "v", "w", "x", "y")], known)
    assert "s-one" not in ids(result)
    assert kinds(result) == ["created", "dormant"]


def test_containment_not_jaccard_when_a_story_doubles():
    # Jaccard here is 0.5 and would fail a 0.6 threshold; containment is 1.0.
    known = {"s-one": urls("a", "b", "c")}
    result = reconcile([urls("a", "b", "c", "d", "e", "f")], known, containment=0.6)
    assert ids(result) == ["s-one"]


class TestTheOrderCandidatesArriveIn:
    """Which id survives a tie is decided by the order the candidates are collected in.

    `reconcile` keeps the largest prior story's id, and `max` returns the first of the
    equal-largest. Once candidates are found through a url index rather than by
    scanning the prior stories in order, that order has to be restored deliberately,
    and nothing else in the output would show it had been lost: the same stories would
    be matched, just under a different surviving id, which is exactly the kind of
    change that makes an accumulated history unjoinable.
    """

    URLS = [f"https://p{i}.test/a" for i in range(4)]

    def test_the_first_of_two_equally_large_priors_keeps_its_id(self):
        known = {"alpha": list(self.URLS), "beta": list(self.URLS)}
        out = reconcile([list(self.URLS)], known)
        assert out["assignments"][0]["id"] == "alpha"

    def test_and_it_is_the_first_by_prior_order_not_by_name(self):
        known = {"beta": list(self.URLS), "alpha": list(self.URLS)}
        out = reconcile([list(self.URLS)], known)
        assert out["assignments"][0]["id"] == "beta"

    def test_a_larger_prior_still_wins_regardless_of_order(self):
        wider = self.URLS + ["https://p9.test/a", "https://p8.test/a"]
        known = {"small": list(self.URLS), "large": wider}
        out = reconcile([list(self.URLS)], known)
        assert out["assignments"][0]["id"] == "large"

    def test_a_cluster_sharing_no_article_matches_nothing(self):
        # The index only ever sees stories sharing an article. This is the property
        # that makes that sound: containment is a positive fraction, so no overlap
        # cannot reach the threshold however it is set.
        known = {"alpha": list(self.URLS)}
        out = reconcile([["https://elsewhere.test/a"]], known)
        assert out["events"][0]["type"] == "created"

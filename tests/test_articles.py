"""Article merge/dedup and sanitation."""

from tensionr.processing.articles import (
    deduce_country,
    merge_and_cap,
    sanitize_data,
    select_new_articles,
)


def test_select_new_drops_missing_urls():
    existing = [{"url": "http://a"}, {"url": None}]
    raw = [{"url": "http://a"}, {"url": None}, {}, {"url": "http://b"}]
    assert select_new_articles(raw, existing) == [{"url": "http://b"}]


def test_merge_dedups_by_url_and_sorts_newest_first():
    new = [{"url": "http://b", "seendate": "20260721T100000Z"}]
    existing = [
        {"url": "http://a", "seendate": "20260720T090000Z"},
        {"url": "http://b", "seendate": "20260719T080000Z"},  # older duplicate
        {"url": None, "seendate": "20260721T230000Z"},  # url-less entries are dropped
    ]
    merged = merge_and_cap(new, existing)
    assert [a["url"] for a in merged] == ["http://b", "http://a"]
    assert merged[0]["seendate"] == "20260721T100000Z"


def test_merge_caps_window():
    articles = [
        {"url": f"http://{i}", "seendate": f"2026072{i % 10}T000000Z"}
        for i in range(30)
    ]
    assert len(merge_and_cap([], articles, cap=10)) == 10


def test_sanitize_strips_injection_chars():
    assert sanitize_data("a<b>{c}[d]\\e") == "abcde"
    assert sanitize_data(None) == ""


def test_deduce_country():
    assert deduce_country("Missile strikes reported near Ukraine border") == "Ukraine"
    assert deduce_country("Local sports roundup") == "Unknown"

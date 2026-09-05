"""GKG row parsing, the URL join, and the schema guard."""

import io
import zipfile

from tensionr.config import GKG_COLUMNS
from tensionr.stories.gkg import fetch, join, parse

URL_A = "https://a.test/one"
URL_B = "https://b.test/two"


def row(url, *, locations="", names="", persons="", orgs="", width=GKG_COLUMNS):
    fields = [""] * width
    if width > 23:
        fields[4], fields[9], fields[11], fields[13], fields[23] = (
            url,
            locations,
            persons,
            orgs,
            names,
        )
    return fields


def zipped(rows) -> bytes:
    body = "\n".join("\t".join(r) for r in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("20260802.gkg.csv", body)
    return buf.getvalue()


def test_locations_take_the_name_out_of_the_hash_separated_record():
    payload = zipped(
        [
            row(
                URL_A,
                locations="4#Strait of Hormuz#IR#IR00#26.5#56.2#-3086420;1#Iran#IR#IR#32#53#IR",
            )
        ]
    )
    rows, _ = parse(payload)
    assert rows[URL_A]["locations"] == ["Strait of Hormuz", "Iran"]


def test_names_drop_the_character_offset():
    payload = zipped([row(URL_A, names="Donald Trump,214;Strait Of Hormuz,908")])
    rows, _ = parse(payload)
    assert rows[URL_A]["names"] == ["Donald Trump", "Strait Of Hormuz"]


def test_persons_and_organisations_are_semicolon_lists():
    payload = zipped(
        [row(URL_A, persons="donald trump;ali khamenei", orgs="white house;irgc")]
    )
    rows, _ = parse(payload)
    assert rows[URL_A]["persons"] == ["donald trump", "ali khamenei"]
    assert rows[URL_A]["organisations"] == ["white house", "irgc"]


def test_empty_fields_produce_empty_lists_not_blank_entries():
    rows, _ = parse(zipped([row(URL_A)]))
    assert rows[URL_A] == {
        "locations": [],
        "names": [],
        "persons": [],
        "organisations": [],
    }


def test_a_row_of_the_wrong_width_is_counted_rather_than_skipped_quietly():
    # This is how a schema change first appears. Absorbing it would turn a broken
    # join into a confident zero.
    payload = zipped([row(URL_A), row(URL_B, width=GKG_COLUMNS - 2)])
    rows, report = parse(payload)
    assert URL_A in rows and URL_B not in rows
    assert report["wrong_width"] == 1
    assert report["rows"] == 2


def test_a_row_without_a_url_is_counted():
    rows, report = parse(zipped([row("")]))
    assert rows == {}
    assert report["no_url"] == 1


def test_the_join_reports_its_rate_and_misses():
    gkg = {
        URL_A: {"locations": ["Iran"], "names": [], "persons": [], "organisations": []}
    }
    result = join([URL_A, URL_B], gkg)
    assert result["rate"] == 0.5
    assert result["misses"] == 1
    assert list(result["matched"]) == [URL_A]


def test_the_join_does_not_normalise_urls():
    # Identifiers are byte-identical between the feeds. Normalising here would hide a
    # mismatch rather than fix one, so a trailing slash is a genuine miss.
    gkg = {URL_A: {"locations": [], "names": [], "persons": [], "organisations": []}}
    assert join([URL_A + "/"], gkg)["rate"] == 0.0


def test_the_join_of_nothing_is_zero_not_an_error():
    assert join([], {})["rate"] == 0.0


def test_the_fetch_report_does_not_shadow_the_rows_it_reports_on(monkeypatch):
    # The report counts rows and the payload is keyed "rows"; merging them replaced
    # the data with an integer, and every caller then failed on len() of an int.
    payload = zipped([row(URL_A, names="Donald Trump,1")])

    class Response:
        status_code = 200
        content = payload

    monkeypatch.setattr(
        "tensionr.stories.gkg.request_with_retry", lambda *a, **k: Response()
    )
    out = fetch(1)
    assert isinstance(out["rows"], dict)
    assert out["rows"][URL_A]["names"] == ["Donald Trump"]
    # one slot, two feeds: the English and the translation file are both read
    assert out["report"]["rows"] == 2


def test_a_field_larger_than_python_default_does_not_abort_the_slot():
    # GKG's GCAM and XML columns run past the 128 KB default, and the reader raised
    # part-way through a real slot, losing every row after it.
    big = "x" * 200_000
    fields = row(URL_A, names="Donald Trump,1")
    fields[17] = big  # V2GCAM
    rows, report = parse(zipped([fields, row(URL_B, names="Ali Khamenei,2")]))
    assert set(rows) == {URL_A, URL_B}, "a row after the oversized one was lost"
    assert report["wrong_width"] == 0

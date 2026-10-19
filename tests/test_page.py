"""The page prints counts straight from private/rows.json, and site/ ships only the free slice.
These pin the three things that went wrong on 2026-10-18: the city's register repeats a licence
row verbatim (LIC432807 eight times) and the count on the page counted every copy; address
title-casing turned Newton into NEwton; and "let their license lapse since April 1" shipped a
licence that lapsed in 2018 and one that expires next March. Run from the repo root: python3 -m pytest -q tests
"""
import gzip, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
D = json.load(open(ROOT / "private" / "rows.json"))
ROWS = D["rows"]
PAGE = (ROOT / "site" / "index.html").read_text()
FREE = json.loads(re.search(r"\nconst FREE=(\{.*?\});\n", PAGE).group(1))
FULL = json.loads(gzip.open(ROOT / "private" / "bundle" / "full.json.gz", "rt").read())["rows"]
PAID = ["manager", "owner", "owner_email", "owner_phone", "heat_permit", "heat_what", "license", "tier", "entity"]


def test_one_row_per_licence():
    licences = [r["license"] for r in ROWS]
    assert len(licences) == len(set(licences)), "the register repeats rows; dedupe on licenceNumber"


def test_addresses_keep_street_names_whole():
    bad = [r["addr"] for r in ROWS if re.search(r"\b(NE|SE|NW|SW)[a-z]", r["addr"])]
    assert not bad, bad  # 'NEwton Ave', 'SEabury Ave'
    assert all(not re.search(r"\s(Ne|Se|Nw|Sw)$", r["addr"]) for r in ROWS)  # directionals stay upper


def test_lapsed_means_expired_this_cycle_and_not_renewed():
    for r in ROWS:
        if r["kind"] == "License lapsed":
            assert D["lapse_since"] <= r["expired"] <= D["pulled"], (r["addr"], r["expired"])
        else:
            assert r["licensed"] >= D["since"], (r["addr"], r["licensed"])


def test_heat_label_agrees_with_the_permit_on_the_row():
    since = D["heat_since"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", since)
    for r in ROWS:
        if r["heat"].startswith("No heating permit"):
            assert r["due"] == 1 and (not r["heat_permit"] or r["heat_permit"] < since), r
            assert r["heat"].endswith(since[:4])
        elif r["heat"].startswith("Heating permit"):
            assert r["due"] == 2 and r["heat_permit"] >= since, r


def test_page_counts_are_the_data():
    n, due, units = len(ROWS), sum(r["due"] == 1 for r in ROWS), sum(r["units"] for r in ROWS)
    assert FREE["total"] == n
    assert f"<h1>{n} Minneapolis rentals" in PAGE
    assert f'stats:[["{n}","rentals' in PAGE and f'["{due}","with no heating permit since {D["heat_since"][:4]}"]' in PAGE
    assert f'["{units:,}","licensed units' in PAGE
    assert f"<b>At {due} of them" in PAGE
    for k, v in FREE["counts"].items():
        assert v == sum(r["kind"] == k for r in ROWS), k
    assert len(FREE["dots"]) == sum(bool(r.get("lat")) for r in ROWS)


def test_site_ships_only_the_free_slice():
    assert len(FREE["rows"]) == 10 and len(FULL) == len(ROWS)
    keys = {k for r in FREE["rows"] for k in r}
    assert not keys & set(PAID), keys & set(PAID)
    full_by_licence = {r["license"]: r for r in FULL}
    for r in FREE["rows"]:
        assert any(f["addr"] == r["addr"] and f["licensed"] == r["licensed"] for f in FULL), r["addr"]
    assert not list((ROOT / "site").rglob("*.gz")) and not (ROOT / "site" / "api" / "_full").exists()
    assert len(full_by_licence) == len(FULL)


def test_entity_regex_catches_a_trailing_co_dot():
    from build import ENT
    assert ENT.search("SMITH PROPERTIES CO.") and ENT.search("ACME CO. ") and ENT.search("JOHN DOE CO.")
    assert not ENT.search("COLIN CONNOR")

"""Rentals that just got a Minneapolis license (or let one lapse), with what the record says
about their heating. Reads private/rentals_raw.json (pipeline/pull.py). Writes private/rows.json.

Why these rows: the city's Rental Property Checklist (7/8/2025) requires a safety check of any
heating plant over 10 years old every two years, on the city's form, by a licensed contractor,
and a newly licensed rental gets its first rental inspection. So the record names two things a
heating contractor wants: a rental the city is about to inspect, and whether its heat has been
replaced inside the ten-year window (a Minneapolis heating permit since Dec 2016).
"""
import json, re, datetime as dt, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"
SINCE = "2026-04-01"
LAPSE_SINCE = "2026-03-01"  # this licence cycle: a lapsed licence is one that expired at this March 1 renewal and was not renewed
REGISTER_START = "2016-12-01"  # the permit register's first month: before it, "no permit" means nothing
KIND = {"CHOWN": "New owner", "CHOWNEXMPT": "New owner", "CONV": "Newly a rental", "CONVEXEMPT": "Newly a rental",
        "ShrtTrmLic": "Short-term rental", "ShrtTrmReg": "Short-term rental"}
# Ends on (?!\w), not \b: "CO." sits before a space or the end of the name, where \b never matches after a dot.
ENT = re.compile(r"\b(LLC|L\.L\.C|INC|CORP|CORPORATION|COMPANY|CO\.|LP|LLP|LTD|TRUST|PROPERTIES|PROPERTY|HOLDINGS|MANAGEMENT|MGMT|PARTNERS|PARTNERSHIP|GROUP|HOUSING|APARTMENTS|INVESTMENTS?|REALTY|RENTALS?|ENTERPRISES|VENTURES|CAPITAL|ASSOCIATES|FOUNDATION|CHURCH)(?!\w)", re.I)
D = lambda s: (s or "")[:10]


def addr_case(a):
    """'3707 NEWTON AVE N' -> '3707 Newton Ave N'; '1 MAIN ST SE' -> '1 Main St SE'. The directional is
    its own word: a plain replace of ' Ne' turned Newton into NEwton (7 rows on 2026-10-17)."""
    a = re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), (a or "").title())
    return re.sub(r"\b(Ne|Se|Nw|Sw)\b", lambda m: m.group(1).upper(), a)


def main():
    import duckdb
    RAW = json.load(open(PRIV / "rentals_raw.json"))
    pulled = RAW["pulled"]
    rows, seen = [], set()
    for x in RAW["licenses"]:
        if x["licenseNumber"] in seen:
            continue  # the register repeats a licence row verbatim (LIC432807 eight times on 2026-10-17)
        lapsed = x["milestone"] == "Delinquent" and x["category"] != "MPHA"
        # Lapsed means the licence has already expired, at this cycle's March 1: a 2018 lapse is not
        # "why now", and a delinquent licence that expires next March has not lapsed yet.
        if lapsed and not (LAPSE_SINCE <= D(x["expirationDate"]) <= pulled):
            continue
        if not lapsed and not (D(x["issueDate"]) >= SINCE and x["category"] in KIND):
            continue
        if not x["latitude"] or not x["apn"]:
            continue
        seen.add(x["licenseNumber"])
        kind = "License lapsed" if lapsed else KIND[x["category"]]
        owner = (x["ownerName"] or "").strip()
        owner = "" if owner == "None" else owner
        units = int(x["licensedUnits"] or 0)
        # Contact is shown when the owner is acting as a business: a company, or a landlord with 5+
        # licensed units. Owners of 1-4 unit rentals are mostly private people: withheld.
        is_ent = bool(ENT.search(owner)) or units >= 5
        rows.append(dict(apn=x["apn"], addr=addr_case(x["address"]),
                         hood=x["neighborhoodDesc"] or "", lat=round(x["latitude"], 5), lon=round(x["longitude"], 5),
                         units=units, kind=kind, licensed=D(x["issueDate"]),
                         expired=D(x["expirationDate"]) if lapsed else "", tier=x["tier"] or "",
                         owner=owner if is_ent else "", owner_email=(x["ownerEmail"] or "") if is_ent else "",
                         owner_phone=(x["ownerPhone"] or "") if is_ent else "", entity=is_ent,
                         manager=(x["applicantName"] or "").strip().title() if is_ent and (x["applicantName"] or "").strip().upper() != owner.upper() else "", license=x["licenseNumber"]))

    # heating permits per parcel
    heat = {}
    for h in RAW["heat"]:
        d = dt.datetime.utcfromtimestamp(h["issueDate"] / 1000).date().isoformat() if h.get("issueDate") else ""
        if d and (h["APN"] not in heat or d > heat[h["APN"]][0]):
            heat[h["APN"]] = (d, (h.get("comments") or "").strip()[:90])
    con = duckdb.connect("/Users/aidan/Desktop/bricks/data/hennepin_gis.duckdb", read_only=True)
    pins = list({r["apn"] for r in rows})
    built = dict(con.execute("select pin, build_yr from parcels where pin in (select unnest(?))", [pins]).fetchall())
    # A heating permit counts when it is inside the ten-year window AND the register could hold it.
    # The row label and the page copy both take their year from this one date, so the words on
    # the page cannot drift from the rule as the window rolls forward.
    TEN = (dt.date.fromisoformat(pulled) - dt.timedelta(days=3652)).isoformat()
    heat_since = max(TEN, REGISTER_START)
    for r in rows:
        b = built.get(r["apn"])
        r["built"] = int(b) if b and str(b).isdigit() and 1800 < int(b) <= 2026 else None
        h = heat.get(r["apn"])
        r["heat_permit"] = h[0] if h else ""
        r["heat_what"] = h[1] if h else ""
        new_bldg = bool(r["built"] and r["built"] >= int(TEN[:4]) + 1)
        if h and h[0] >= heat_since:
            r["heat"] = "Heating permit " + h[0][:4]
            r["due"] = 2
        elif new_bldg:
            r["heat"] = f"Built {r['built']}, heat under 10 years"
            r["due"] = 3
        else:
            r["heat"] = f"No heating permit since {heat_since[:4]}"
            r["due"] = 1
        del r["apn"]
    rows.sort(key=lambda r: (r["due"], -int(r["licensed"].replace("-", "") or 0)))
    json.dump({"pulled": pulled, "since": SINCE, "lapse_since": LAPSE_SINCE, "heat_since": heat_since, "rows": rows}, open(PRIV / "rows.json", "w"))
    print("rows", len(rows), collections.Counter(r["kind"] for r in rows), collections.Counter(r["heat"].split(" 2")[0] if r["due"] != 3 else "new" for r in rows))
    print("entity owners", sum(r["entity"] for r in rows), "with email", sum(bool(r["owner_email"]) for r in rows), "built known", sum(bool(r["built"]) for r in rows))
    print("units", sum(r["units"] for r in rows), "due", sum(r["due"] == 1 for r in rows))


if __name__ == "__main__":
    main()

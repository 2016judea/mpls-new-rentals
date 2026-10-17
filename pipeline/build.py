"""Rentals that just got a Minneapolis license (or let one lapse), with what the record says
about their heating. Reads private/rentals_raw.json (pipeline/pull.py). Writes private/rows.json.

Why these rows: the city's Rental Property Checklist (7/8/2025) requires a safety check of any
heating plant over 10 years old every two years, on the city's form, by a licensed contractor,
and a newly licensed rental gets its first rental inspection. So the record names two things a
heating contractor wants: a rental the city is about to inspect, and whether its heat has been
replaced inside the ten-year window (a Minneapolis heating permit since Dec 2016).
"""
import json, re, datetime as dt
from pathlib import Path
import duckdb
ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"
RAW = json.load(open(PRIV / "rentals_raw.json"))
SINCE = "2026-04-01"
KIND = {"CHOWN": "New owner", "CHOWNEXMPT": "New owner", "CONV": "Newly a rental", "CONVEXEMPT": "Newly a rental",
        "ShrtTrmLic": "Short-term rental", "ShrtTrmReg": "Short-term rental"}
ENT = re.compile(r"\b(LLC|L\.L\.C|INC|CORP|CORPORATION|COMPANY|CO\.|LP|LLP|LTD|TRUST|PROPERTIES|PROPERTY|HOLDINGS|MANAGEMENT|MGMT|PARTNERS|PARTNERSHIP|GROUP|HOUSING|APARTMENTS|INVESTMENTS?|REALTY|RENTALS?|ENTERPRISES|VENTURES|CAPITAL|ASSOCIATES|FOUNDATION|CHURCH)\b", re.I)
D = lambda s: (s or "")[:10]

rows = []
for x in RAW["licenses"]:
    lapsed = x["milestone"] == "Delinquent" and x["category"] != "MPHA"
    if not lapsed and not (D(x["issueDate"]) >= SINCE and x["category"] in KIND):
        continue
    if not x["latitude"] or not x["apn"]:
        continue
    kind = "License lapsed" if lapsed else KIND[x["category"]]
    owner = (x["ownerName"] or "").strip()
    owner = "" if owner == "None" else owner
    units = int(x["licensedUnits"] or 0)
    # Contact is shown when the owner is acting as a business: a company, or a landlord with 5+
    # licensed units. Owners of 1-4 unit rentals are mostly private people: withheld.
    is_ent = bool(ENT.search(owner)) or units >= 5
    rows.append(dict(apn=x["apn"], addr=re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), x["address"].title()).replace(" Ne", " NE").replace(" Se", " SE").replace(" Nw", " NW").replace(" Sw", " SW"),
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
TEN = (dt.date.today() - dt.timedelta(days=3652)).isoformat()
for r in rows:
    b = built.get(r["apn"])
    r["built"] = int(b) if b and str(b).isdigit() and 1800 < int(b) <= 2026 else None
    h = heat.get(r["apn"])
    r["heat_permit"] = h[0] if h else ""
    r["heat_what"] = h[1] if h else ""
    new_bldg = bool(r["built"] and r["built"] >= int(TEN[:4]) + 1)
    if h and h[0] >= TEN:
        r["heat"] = "Heating permit " + h[0][:4]
        r["due"] = 2
    elif new_bldg:
        r["heat"] = f"Built {r['built']}, heat under 10 years"
        r["due"] = 3
    else:
        r["heat"] = "No heating permit since 2016"
        r["due"] = 1
    del r["apn"]
rows.sort(key=lambda r: (r["due"], r["kind"] == "License lapsed", r["licensed"][::-1] and "", ), reverse=False)
rows.sort(key=lambda r: (r["due"], -int(r["licensed"].replace("-", "") or 0)))
json.dump({"pulled": RAW["pulled"], "since": SINCE, "rows": rows}, open(PRIV / "rows.json", "w"))
import collections
print("rows", len(rows), collections.Counter(r["kind"] for r in rows), collections.Counter(r["heat"].split(" 2")[0] if r["due"] != 3 else "new" for r in rows))
print("entity owners", sum(r["entity"] for r in rows), "with email", sum(bool(r["owner_email"]) for r in rows), "built known", sum(bool(r["built"]) for r in rows))
print("units", sum(r["units"] for r in rows), "due", sum(r["due"] == 1 for r in rows))

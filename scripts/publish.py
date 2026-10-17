#!/usr/bin/env python3
"""Write site/index.html (free slice) and private/bundle/full.json.gz (the paid list) from
private/rows.json (pipeline/build.py). Every number on the page is computed here."""
import json, datetime as dt
from sitekit import render
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT / "private" / "rows.json"))
rows = D["rows"]
ORDER = ["New owner", "Newly a rental", "Short-term rental", "License lapsed"]
PAID = ["manager", "owner", "owner_email", "owner_phone", "heat_permit", "heat_what", "license", "tier", "entity"]
due = sum(r["due"] == 1 for r in rows); units = sum(r["units"] for r in rows); ent = sum(r["entity"] for r in rows)
pulled = dt.date.fromisoformat(D["pulled"]).strftime("%b %-d, %Y")
sample = sorted([r for r in rows if r["kind"] != "License lapsed"], key=lambda r: r["licensed"], reverse=True)[:8] + \
         [r for r in rows if r["kind"] == "License lapsed"][:2]
RIVER = [[45.052,-93.2885],[45.03,-93.2805],[45.012,-93.2745],[44.998,-93.2685],[44.988,-93.2625],[44.9815,-93.2575],[44.977,-93.2475],[44.972,-93.2385],[44.967,-93.2295],[44.962,-93.2225],[44.953,-93.2065],[44.946,-93.2005],[44.935,-93.2005],[44.917,-93.2035],[44.905,-93.1995],[44.889,-93.1935]]
COLS = [("kind","Why it's on the list"),("addr","Address"),("hood","Neighborhood"),("units","Licensed units"),("licensed","License issued"),("expired","License expired (lapsed only)"),("built","Year built"),("heat","Heating on record"),("heat_permit","Last heating permit"),("heat_what","Heating permit description"),("owner","Owner (companies and 5+ unit landlords)"),("manager","License applicant"),("owner_email","Owner email"),("owner_phone","Owner phone"),("license","License #"),("tier","City tier")]
cfg = """{chipKey:"kind",chipOrder:%s,river:%s,csv:"new-minneapolis-rentals.csv",cols:%s,
 stats:[["%d","rentals licensed since April 1, or lapsed"],["%d","with no heating permit since 2016"],["%s","licensed units in all"]],
 legend:[["var(--hot)","No heating permit since 2016"],["var(--accent)","Heating permit since 2016"]],
 dotColor:["var(--accent)","var(--accent)","var(--accent)","var(--done)"],
 color:r=>r.due===1?"var(--hot)":"var(--accent)",
 title:r=>r.addr, what:r=>r.heat+(r.built?` · built ${r.built}`:""),
 tag:r=>`<span class="tag ${r.due===1?"hot":""}">${r.kind}</span>`,
 meta:r=>[r.hood,r.units?(r.units+(r.units===1?" unit":" units")):"",r.kind==="License lapsed"?("Expired "+fmt(r.expired)):("Licensed "+fmt(r.licensed))],
 paid:r=>[r.owner?`Owner: ${esc(r.owner)}`:"Owner of a 1 to 4 unit rental (not shown)",r.manager?`Applicant: ${esc(r.manager)}`:"",r.owner_phone?`<a href="tel:${esc(r.owner_phone)}">${esc(r.owner_phone)}</a>`:"",r.owner_email?`<a href="mailto:${esc(r.owner_email)}">${esc(r.owner_email)}</a>`:"",r.heat_permit?`Heating permit ${fmt(r.heat_permit)}: ${esc(r.heat_what)}`:""].filter(Boolean).join(" · "),
 sorts:[["newest","Newest license first",false],["due","Heating check most likely due",true],["units","Most units first",true],["hood","By neighborhood",false]],
 sortFn:{newest:r=>r.sort((a,b)=>(b.licensed||b.expired).localeCompare(a.licensed||a.expired)),due:r=>r.sort((a,b)=>(a.due-b.due)||b.units-a.units||b.licensed.localeCompare(a.licensed)),units:r=>r.sort((a,b)=>b.units-a.units),hood:r=>r.sort((a,b)=>a.hood.localeCompare(b.hood))},
 lockText:n=>`${n} more rentals, owner contacts, and the heating-check-due sort`}""" % (json.dumps(ORDER), json.dumps(RIVER), json.dumps(COLS), len(rows), due, f"{units:,}")
LIGHT = '--bg:#f6f3ee;--panel:#ece7df;--ink:#211a14;--ink2:#41372e;--muted:#6f655b;--rule:#d9d1c5;--accent:#2e5a6b;--onaccent:#f6f3ee;--hot:#c2501f;--done:#9a9085;--ghost:#cbc3b7;--water:#8fb0bf;--tagbg:#e6e0d6;--tagfg:#4d443b;--hotbg:#f5dccd;--hotfg:#8f3510;--display:"Fraunces",Georgia,serif;--body:"Public Sans",system-ui,sans-serif;--h1w:600;'
DARK = '--bg:#16130f;--panel:#1f1a15;--ink:#eee7de;--ink2:#cbc1b5;--muted:#958a7e;--rule:#342c24;--accent:#7fb4c9;--onaccent:#16130f;--hot:#f08a58;--done:#776d62;--ghost:#3a322a;--water:#3e6475;--tagbg:#2a231d;--tagfg:#bcb1a4;--hotbg:#47250f;--hotfg:#f6b994;'
counts = render(rows=rows, sample=sample, paid_fields=PAID, chip_key="kind", chip_order=ORDER, cfg_js=cfg, site="mpls-new-rentals", subs={
 "__TITLE__": "New Minneapolis Rentals",
 "__DESC__": f"{len(rows)} Minneapolis rentals licensed since April 1, 2026 or lapsed, with what the city record says about their heating.",
 "__FONTS__": "family=Fraunces:opsz,wght@9..144,600&family=Public+Sans:wght@400;500;600",
 "__LIGHT__": LIGHT, "__DARK__": DARK,
 "__EYEBROW__": f"For furnace and rental-inspection contractors · Minneapolis public records · updated {pulled}",
 "__H1__": f"{len(rows)} Minneapolis rentals with a new license, and what the record says about their heat",
 "__LEDE__": f"Minneapolis requires a safety check of any rental heating plant over ten years old every two years, and a newly licensed rental gets its first city inspection. These are the rentals that changed owners, became rentals, or let their license lapse since April 1. <b>At {due} of them the city has no heating permit on file since 2016</b>, so the furnace or boiler is likely past ten years.",
 "__MAPLABEL__": "Map of Minneapolis with each rental as a dot",
 "__NOTE__": f"<p>Sources, all public: the City of Minneapolis rental license register and building permit register, pulled {pulled}, and Hennepin County parcel records for year built. The ten-year rule is from the city's Rental Property Checklist (July 2025); the city's HVAC safety check form is valid for two years.</p><p>How heat is read. A heating permit is a Minneapolis mechanical permit at the same parcel whose description names a furnace, boiler, heat pump or heating work. The register starts in December 2016, so \"no heating permit since 2016\" means none on record, not proof of the age of the plant. In a building with several units, one permit may cover one unit.</p><p>Owner contact is shown for companies and for landlords with five or more licensed units, as the city publishes it. Owners of one to four unit rentals are left unnamed. Minneapolis only. MPHA public housing is left out.</p><p>From Aidan Jude at Brick &amp; Mortar (aidan@brickandmortar.dev).</p>"})
print("rows", len(rows), "due", due, "units", units, "owner contact shown", ent, "with email", sum(bool(r["owner_email"]) for r in rows), counts, "sample", len(sample))

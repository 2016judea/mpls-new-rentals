"""Pull the Minneapolis rental-license register and every heating permit since the register's
start (Dec 2016), then join year built from Hennepin County. Writes private/rentals_raw.json.

    python3 pipeline/pull.py
"""
import json, re, urllib.request, urllib.parse, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"
B = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services"

def q(svc, where, fields):
    out, off = [], 0
    while True:
        p = dict(where=where, outFields=fields, f="json", resultOffset=off, resultRecordCount=2000, returnGeometry="false")
        d = json.load(urllib.request.urlopen(urllib.request.Request(f"{B}/{svc}/FeatureServer/0/query", data=urllib.parse.urlencode(p).encode()), timeout=120))
        fs = [f["attributes"] for f in d.get("features", [])]
        out += fs
        if not d.get("exceededTransferLimit") or not fs:
            return out
        off += len(fs)

lic = q("Active_Rental_Licenses", "1=1",
        "apn,licenseNumber,category,milestone,tier,status,issueDate,expirationDate,address,ownerName,ownerEmail,ownerPhone,applicantName,licensedUnits,neighborhoodDesc,shortTermRental,latitude,longitude")
print("licenses", len(lic))
# Heating permits: mechanical permits whose description names the heating plant.
HEAT = re.compile(r"furnace|boiler|heat ?pump|heating|hydronic|unit heater|rtu|rooftop", re.I)
mech = q("CCS_Permits", "permitType='Mechanical'", "APN,Display,comments,issueDate,status,permitNumber")
heat = [m for m in mech if m.get("APN") and HEAT.search(m.get("comments") or "")]
print("mechanical", len(mech), "heating", len(heat))
json.dump({"pulled": dt.date.today().isoformat(), "licenses": lic, "heat": heat}, open(PRIV / "rentals_raw.json", "w"))

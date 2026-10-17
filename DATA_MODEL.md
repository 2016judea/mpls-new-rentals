# Data model: New Minneapolis Rentals

Written from the need alone (BUSINESS.md rule 5), then checked against what exists, 2026-10-17.

**The need.** A heating contractor who does rental-license safety checks
(first prospect: a Craigslist post, 10/05: *"We perform Minneapolis, St Paul, St Louis Park,
New Hope and other cities Rental License and Tish Report Safety Checks on Furnaces"*) wants the
rentals whose owner is about to need a heating safety certificate, and who to call.

## Ideal model

**Rental property** (one per licensed address)

| field | answers |
|---|---|
| address, lat/lon, neighborhood | where is the job, and is it on my route |
| licensed units | how many furnaces / certificates (one form per unit) |
| why now: new owner, newly a rental, short-term, lapsed | why this owner is dealing with the city right now |
| license issued / expired date | how fresh the trigger is |
| next city rental inspection date | when the certificate is actually due |
| heating plant age (or last replacement) | is it over 10 years, so a check is required |
| last HVAC safety certificate date | has someone already done it (valid 2 years) |
| owner, owner phone/email, applicant | who to call |

**Heating permit** (joins on parcel): date, description. Answers "replaced inside 10 years?"

## Reality, field by field

| field | source | filled? |
|---|---|---|
| address, units, kind, dates, neighborhood | Minneapolis `Active_Rental_Licenses` (ArcGIS, daily) | yes, all 980 rows |
| next inspection date | not published | **no**: proxied by the license date (a new license gets a first inspection) |
| "expiring in the next 90 days" | every license expires 3/1/2027 (22,421 of 23,324 rows) | **no spread**: reframed to *new and lapsed* licenses |
| heating plant age | Minneapolis permits register, mechanical permits naming furnace/boiler/heat pump, back to Dec 2016 | partial: a permit proves a recent plant; no permit means none on record since 2016, not proof of age |
| last safety certificate | emailed to the inspector, never published | **no** |
| year built | Hennepin County parcels | 943 of 980 |
| owner contact | published by the city for 411 of 438 recent licenses | shown for companies and 5+ unit landlords (134 rows); owners of 1-4 unit rentals are private people and are held back pending Aidan's call |
| TISH (homes about to sell) | no Minneapolis open dataset of Truth-in-Sale-of-Housing evaluations among the city's 200+ ArcGIS services (checked 10/17) | **no**: dropped |

Verdict: build. The two dead fields (inspection date, certificate date) are replaced by the
license date and the heating-permit join, which is the reasoning step the contractor does by hand.

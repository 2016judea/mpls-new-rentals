# New Minneapolis Rentals

**Live:** https://mpls-new-rentals.vercel.app

Every Minneapolis rental that got a new license since April 1, 2026 (new owner, newly a
rental, short-term) or let one lapse, with what the city record says about its heating.
Minneapolis requires a safety check of any rental heating plant over ten years old every two
years, and a newly licensed rental gets its first city inspection. This list joins the city's
rental-license register to its permit register: a rental with no heating permit on file since
2016 likely has a plant past ten years, and needs the check.

Built for furnace and rental-inspection contractors. First prospect: a Craigslist post (10/05)
offering *"Rental License and Tish Report Safety Checks on Furnaces"*.

## Free and paid

| | what | why |
|---|---|---|
| free | the count, the map of every rental, counts by reason, and 10 real rows with heating status and year built | proves the join on real addresses before anyone pays |
| **$5** | all 952 rows; owner, phone and email (companies and 5+ unit landlords); license applicant; the last heating permit and its description; the **heating check most likely due** sort; the spreadsheet | the poster sells the check itself: the part they act on is *which* rental needs it and *who* to call |

## Price

$5 once. Set by Aidan on 2026-10-17 for all three products in this round. **A hypothesis:**
one rental safety check is a job worth roughly $100 to $150, so one booked job pays for the list
about twenty times. Revise on checkout-vs-payment evidence.

## The paywall

Ported from `~/Desktop/msp-house-index` via `salon-rates` (`product-paywall` skill).
`site/` ships only the free slice; `scripts/publish.py` writes the full list to
`private/bundle/full.json.gz` (gitignored) and `scripts/deploy.py` uploads it as `api/_full/`,
which only `/api/data` reads.

| route | does |
|---|---|
| `POST /api/checkout` | Stripe embedded Checkout, $5, mints the password into session metadata + invoice |
| `POST /api/stripe-webhook` | emails the buyer the password (Mailgun), once |
| `GET /api/session-status` | the return page's check; sends the password if the webhook has not |
| `GET /api/data` | password in `x-password`: HMAC check, then a paid session in Stripe |

Comp password: `python3 scripts/issue_password.py "comp:<label>"`. A lost password:
`python3 scripts/fulfil.py <session_id>`. Vercel env: `STRIPE_SECRET_KEY`,
`STRIPE_WEBHOOK_SECRET`, `ACCESS_SECRET`, `MAILGUN_*`, `SITE_URL`.

## Run it

    python3 pipeline/pull.py      # rental licenses + every heating permit (~2 min)
    python3 pipeline/build.py     # join, year built from bricks/data/hennepin_gis.duckdb
    cd scripts && python3 publish.py && python3 deploy.py   # VERCEL_TOKEN in env

Sources: City of Minneapolis rental license register and permit register (ArcGIS open data),
Hennepin County parcels. See `DATA_MODEL.md` for what each field answers and which could not be filled.

MIT licence.

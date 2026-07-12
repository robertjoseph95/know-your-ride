# Know Your Ride

**Your pocket owner's manual for every car.** A free vehicle-maintenance reference that puts oil specs, torque values, parts, fluids, recalls, complaints, repair guides, and live diagnostics for thousands of vehicles in one place.

🔧 Live: **[knowyourride.net](https://knowyourride.net)**

---

## What it is

Know Your Ride is a maintenance-reference web app backed by a curated SQLite database of vehicle specifications. Pick your car from the garage and get the exact figures a home mechanic needs — no ad-walls, no PDF hunting.

Coverage: **1,600+ modern vehicles (2003–2025) with full specs**, plus **1,600+ older vehicles (1981–2002)** with year/make/model identification (marked *Partial data*), and **5,000+ OBD-II diagnostic trouble codes**.

## Features

- **Garage specs** — oil viscosity/type/capacity, drain bolt torque & socket, spark plugs & gap, filters, tires & pressures, batteries, fluids, and a full torque-spec table per vehicle.
- **VIN decode** — paste a 17-character VIN to jump straight to the matching vehicle (NHTSA vPIC).
- **DTC code lookup** — search any P/B/C/U trouble code; for supported codes, see **CarMD-style ranked fixes** with success probability, average cost, and severity.
- **AI repair guides** — concise, spec-grounded DIY walkthroughs (Claude) that use only verified figures from the database and refuse to guess safety-critical torque values.
- **YouTube DIY videos** — relevant how-to videos surfaced per vehicle + service.
- **Know Your Part** — snap a photo of a part and get it identified (Claude vision, with strict cost controls).
- **Vehicle Value** — one-tap Kelley Blue Book trade-in / private-party value lookup, pre-filled by year/make/model.
- **Safety** — NHTSA recalls (with "do not drive" flags), complaints, crash ratings, and reliability signals.
- **OBD-II panel** — live diagnostics readout (when paired with a compatible adapter via the local server).
- **SEO landing pages** — static per-vehicle and per-code pages with a generated `sitemap.xml`.

## Tech stack

- **Data:** SQLite (`wrench_vehicles.db`) assembled from NHTSA (vPIC, recalls, complaints, safety), EPA fuel-economy, and the Vehicle Finder API.
- **Frontend:** a single self-contained `index.html` (vanilla JS) with the vehicle data embedded as JSON at build time.
- **Backend:** Vercel Python serverless functions (`api/`) for VIN decode, YouTube search, AI guides, and part identification.
- **Infra:** Vercel (Fluid Compute, Python runtime) + Upstash Redis (caching, rate-limiting, and cost budgets).
- **AI:** Anthropic Claude (`claude-sonnet-4-6`) for repair guides and part-image identification.

## Repository layout

```
index source        wrench_demo.html        # the app; built into wrench_deploy/index.html
build pipeline       files/04_rebuild_demo.py # rebuilds the embedded data + injects features
                     wrench_seo.py            # generates SEO pages + sitemap.xml + robots.txt
                     wrench_vpic_backfill.py  # loads pre-2003 vehicles from NHTSA vPIC
                     wrench_*.py              # one-off data backfill / enrichment scripts
local server         wrench_serve.py          # dev proxy for the API endpoints
deploy target        wrench_deploy/           # Vercel project (index.html, api/, vehicles/, dtc/)
```

## Configuration

API keys are **never** committed. Locally, the dev server reads them from `wrench_config.json` (git-ignored):

```json
{
  "anthropic_api_key": "sk-ant-...",
  "youtube_api_key": "AIza...",
  "vehicle_finder_api_key": "vda_..."
}
```

The backfill scripts read the Vehicle Finder key from the `VEHICLE_FINDER_KEY` environment variable.

In production (Vercel), set these as project environment variables:

| Variable | Used by |
|---|---|
| `ANTHROPIC_API_KEY` | `api/guide.py`, `api/identify-part.py` |
| `YOUTUBE_API_KEY` | `api/youtube.py` |
| `VEHICLE_FINDER_KEY` | backfill scripts |
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` | Redis cache, rate-limits, budgets |

### Key rotation (quarterly)

Rotate these secrets every quarter in their respective dashboards **and** update the matching
Vercel environment variables (and local `wrench_config.json`):

| Key | Rotate in | Notes |
|---|---|---|
| Anthropic API key | console.anthropic.com | powers AI guides + part scanner |
| YouTube API key | Google Cloud Console | restrict by referrer/IP |
| Stripe keys (secret + webhook secret) | dashboard.stripe.com | live mode |

- **Last rotated:** 2026-05-30
- **Next rotation due:** 2026-08-30

(The Vehicle Finder key was retired 2026-05-30 — no longer needed.)

## Local development

```bash
# 1. add wrench_config.json with your keys (see above)
# 2. run the dev server (serves the demo + proxies the APIs)
python wrench_serve.py
# 3. open http://localhost:8000/
```

## Build

```bash
# rebuild the demo from the database (re-embeds data, re-injects features)
python files/04_rebuild_demo.py

# regenerate SEO pages + sitemap
python wrench_seo.py

# copy the built demo into the deploy folder
cp wrench_demo.html wrench_deploy/index.html
```

## Deploy

**To deploy: commit your changes and `git push` to `main`.** That's it.

```bash
# Targeted add ONLY. The working tree holds untracked copyrighted OEM text and
# private business/DoD docs; `git add -A` / `git add .` would ship them into this
# PUBLIC repo. Stage each intended path explicitly and verify before pushing.
git add wrench_deploy/index.html wrench_demo.html   # + any other paths you changed
git status                                          # confirm nothing unintended is staged
git commit -m "your message"
git show --stat HEAD                                # verify the commit's file list
git push origin main
```

The Vercel project is connected to this GitHub repo with its **Root Directory set to
`wrench_deploy`**, so every push to `main` automatically builds and deploys production
(knowyourride.net) from that folder.

> ⚠️ **Do not use `npx vercel --prod` or `vercel deploy wrench_deploy`.** Because the
> project's Root Directory is already `wrench_deploy`, passing that path doubles it
> (`wrench_deploy/wrench_deploy`) and the command fails. Git push is the only supported
> deploy path. (If you ever must deploy via CLI, run `vercel deploy --prod` from the repo
> root with no path argument.)

## Data sources

- **NHTSA** — vPIC (VIN decode & vehicle catalog), recalls, complaints, safety ratings.
- **EPA** — fuel economy and engine data (fueleconomy.gov).
- **Vehicle Finder API** — maintenance specifications.
- **Kelley Blue Book** — vehicle valuation (linked out, not scraped).

DTC fix-probability data is derived from openly available diagnostic datasets.

## License

Personal project. Vehicle data belongs to its respective sources; this project is a reference aggregator and is not affiliated with any manufacturer, NHTSA, EPA, or Kelley Blue Book.

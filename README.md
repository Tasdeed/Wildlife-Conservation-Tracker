# Wildlife Conservation Tracker

Tracks IUCN Red List species, predicts population trends with a Random Forest
model, and visualizes it all in a React dashboard.

**Live:** https://tasdeed.github.io/Wildlife-Conservation-Tracker/
· API: https://wildlife-conservation-tracker.onrender.com

Both run on free tiers that sleep when idle, so the first load after a quiet
period takes 30–60 seconds. Everything is quick once warm.

- **Backend** — Flask API + PostgreSQL, scikit-learn model, IUCN Red List v4 loaders
- **Frontend** — React + Vite + TypeScript + Tailwind (dashboard, species browser, ML
  predictions, range map)

## Architecture

```
frontend/ (React + Vite)  ──HTTP──▶  backend/ (Flask API)  ──▶  PostgreSQL
   GitHub Pages                          Render                     Neon
```

The frontend is a static SPA that calls the Flask API; it never touches the
database directly. All four data views read from these endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/model/stats` | Dashboard counts + model info |
| `GET /api/species?category=&trend=&limit=` | Filterable species list |
| `GET /api/species/<id>` | Species detail |
| `GET /api/predict/<id>` | ML trend prediction + confidence |
| `GET /api/locations?category=&trend=` | Map markers (country centroids) |

### Data model

Two tables. `species` (966 rows) holds taxonomy, IUCN category and population
trend; `species_locations` (2118 rows across 942 species) holds country
centroids, one species to many points. Created by `db.create_all()` via
`flask --app app init-db` — there are no migrations, so column changes need
hand-written DDL.

## Local development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # then fill in IUCN_API_TOKEN and SECRET_KEY
createdb wildlife_tracker      # local Postgres
flask --app app init-db        # create tables
python load_species_data.py    # seed species from IUCN (taxonomy + trend, one pass)
python populate_locations.py   # fetch country ranges for the map
python train_model.py          # train + save ml_model.pkl
python app.py                  # serves http://localhost:5001
```

`SECRET_KEY` is required — the app raises at startup without it, rather than
falling back to a default that would be public in this repo.

**Database selection.** `.env.example` points `DATABASE_URL` at local
Postgres, which is what a fresh clone gets. If a Neon branch is linked (see
below), the repo-root `.env.local` is loaded first and overrides it, so the app
talks to Neon instead; `backend/.env` still supplies the IUCN token and secret
key. Comment out `DATABASE_URL` in `backend/.env` to make that override
unambiguous, or leave it set to fall back to local Postgres when no branch is
linked.

### Growing the dataset over time

`load_batch.py` adds a bounded, balanced batch of new species each run (up to
1000/category, ~5000 total) and retrains — run it repeatedly to accumulate data
without hammering the rate-limited IUCN API in one go:

```bash
python load_batch.py                     # add ~60/category + retrain on real labels
python load_batch.py --per-category 100  # larger batch this run
python load_batch.py --with-locations    # also backfill map markers for new species
python load_batch.py --no-train          # load only
```

It skips species already loaded (resumable) and, unlike `train_model.py`, trains
only on real IUCN trend labels — it never persists model predictions back as
labels, so repeated runs don't create a self-training feedback loop.

### Frontend

```bash
cd frontend
npm ci
npm run dev    # http://localhost:5173/Wildlife-Conservation-Tracker/
```

`frontend/.env.local` points the dev app at `http://localhost:5001`.

**Test frontend changes from a clean clone, not the working tree.** Ignored
files still exist on your disk, so a local build can pass while CI fails:

```bash
git clone <repo> /tmp/check && cd /tmp/check/frontend && npm ci && npm run build
```

Three separate deploys failed to exactly this — see Known issues.

## Deployment

| Piece | Host | How |
|-------|------|-----|
| Frontend | **GitHub Pages** | `.github/workflows/deploy.yml`, on pushes to `main` touching `frontend/**` |
| Backend | **Render** | free web service, root dir `backend`, `gunicorn app:app` |
| Database | **Neon** | project `super-wildflower-71352044`, branch `production`, aws-us-east-2 |

### Neon

The repo is linked with the Neon CLI. `neon env pull` writes `DATABASE_URL`,
`DATABASE_URL_UNPOOLED` and `NEON_BRANCH` into the git-ignored root
`.env.local`; `neon.ts` declares the services. Use the **pooled** URL for the
app and the **unpooled** one for dumps and migrations.

To seed a fresh branch, copy the local database rather than re-running the
loaders — that takes ~25 minutes against the rate-limited IUCN API and
produces a different dataset:

```bash
pg_dump --no-owner --no-privileges wildlife_tracker | psql "$DATABASE_URL_UNPOOLED"
```

### Render

Set up through the dashboard's manual form, **not** the `render.yaml`
blueprint, so the blueprint's `envVars` are not applied. These are entered by
hand and can drift from the committed file:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.12.7` — required; the pinned numpy/pandas/scikit-learn have no cp313 wheels, and Render's default would build them from source and fail |
| `DATABASE_URL` | the pooled Neon URL |
| `SECRET_KEY` | any random string |

Root Directory must be `backend`; build `pip install -r requirements.txt`,
start `gunicorn app:app`.

### GitHub Pages

Repo Settings → Pages → Source must be **GitHub Actions** (not "Deploy from a
branch"), or the workflow's deploy step fails. `vite.config.ts`'s `base` must
match the repository name's capitalisation exactly. The app uses `HashRouter`
so the Pages subpath works without server-side routing.

## Notes

- **Secrets**: `backend/.env` and the root `.env.local` are git-ignored.
  `frontend/.env.production` is committed on purpose — it holds the public API
  URL and the CARTO basemap key, both of which the Pages build bakes into the
  bundle. Those are client-side values the browser sends itself, so they are
  public regardless; the control for the CARTO key is a domain restriction in
  the CARTO dashboard, not secrecy. No server-side secret belongs in that file.
- **`.gitignore` is split by directory**: `backend/`, `frontend/` and the root
  each own their rules. Don't merge language templates back into the root; see
  Known issues.
- **Map data**: IUCN provides country-level ranges, so markers are plotted at
  country centroids — approximate by design, not precise sightings.

## The model, honestly

A Random Forest predicting IUCN population trend. In practice it's binary:
of 966 species, 631 are Decreasing, 325 Stable, 9 Unknown and 1 Increasing.

Accuracy depends entirely on how you measure it:

| Protocol | Accuracy | Majority baseline |
|----------|----------|-------------------|
| Random split, all features | 95% | 66% |
| Grouped by family, pooled out-of-fold | 73% | 66% |
| **Grouped, pooled, uncontaminated rows only** | **67%** | **58%** |

Only the last row is defensible, for two reasons.

**Taxonomic leakage.** A random split puts members of the same family in both
train and test, so the model memorises "this family is Decreasing" rather than
learning anything. Holding out whole families drops it from 95% to 73%. Nearly
all remaining signal is in `order` alone — `order` by itself matches the full
feature set.

**Label contamination.** `train_model.py` writes its own predictions back into
`species.population_trend` for Unknown species, and there's no column recording
which labels are real. It has run at least once: the March 2026 cohort (191
rows) has zero Unknown remaining while the July cohort has 9. Evaluating on
those rows scores the model partly against its own earlier output. Filtering to
`created_at >= 2026-06-01` gives the 67% figure.

IUCN category is excluded from the honest figure: Red List status is assigned
partly on population decline, so it partially encodes the target — and on
uncontaminated data it actively hurts (64% vs 67%).

The species detail view shows predicted vs. recorded trend with a weak-signal
caveat, so the model's limits are visible in the UI.

## Known issues

- **`train_model.py` writes predictions into the labels column** (the
  contamination above). It should be removed, and a `trend_source` column added,
  before anything like it is re-enabled. `load_batch.py` already avoids it.
- **Render config drift** — the service was created from the manual form, so
  `render.yaml` documents intent but isn't the source of truth.
- **No migrations** — `db.create_all()` only creates missing tables; it will not
  alter existing ones.
- **`.gitignore` history** — the root file was once a concatenated Python + Node
  template whose unanchored patterns matched at any depth. `*.pkl` excluded the
  trained model, `package-lock.json` broke `npm ci`, and `lib/` excluded
  `frontend/src/lib/` entirely, leaving the repo unbuildable by anyone cloning
  it. All three are fixed by the per-directory split.

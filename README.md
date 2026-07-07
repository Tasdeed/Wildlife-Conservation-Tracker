# Wildlife Conservation Tracker

Tracks IUCN Red List species, predicts population trends with a Random Forest
model, and visualizes it all in a React dashboard.

- **Backend** — Flask API + PostgreSQL, scikit-learn model, IUCN Red List v4 loaders
- **Frontend** — React + Vite + TypeScript + Tailwind (dashboard, species browser, ML
  predictions, range map)

## Architecture

```
frontend/ (React + Vite)  ──HTTP──▶  backend/ (Flask API)  ──▶  PostgreSQL
   GitHub Pages                          Render                     Neon
```

The frontend is a static SPA that calls the Flask API. All four data views read
from these endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/model/stats` | Dashboard counts + model info |
| `GET /api/species?category=&trend=&limit=` | Filterable species list |
| `GET /api/species/<id>` | Species detail |
| `GET /api/predict/<id>` | ML trend prediction + confidence |
| `GET /api/locations?category=&trend=` | Map markers (country centroids) |

## Local development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in IUCN_API_TOKEN
createdb wildlife_tracker      # local Postgres
flask --app app init-db        # create tables
python load_species_data.py    # seed species from IUCN (taxonomy + trend, one pass)
python populate_locations.py    # fetch country ranges for the map
python train_model.py           # train + save ml_model.pkl
python app.py                   # serves http://localhost:5001
```

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
npm install
npm run dev                     # http://localhost:5173/wildlife-conservation-tracker/
```

`frontend/.env.local` points the dev app at `http://localhost:5001`.

## Deployment (free tiers)

| Piece | Host | Notes |
|-------|------|-------|
| Frontend | **GitHub Pages** | Built + published by `.github/workflows/deploy.yml` on push to `main` |
| Backend | **Render** | `render.yaml` blueprint; sleeps when idle (cold start ~30–60s) |
| Database | **Neon** | Persistent free Postgres; set `DATABASE_URL` in Render |

Steps:

1. **Neon** — create a project, copy the connection string.
2. **Render** — deploy from `render.yaml`; set `DATABASE_URL` to the Neon string.
   Then run the loaders once against Neon to populate it (shell into the service or
   run locally with `DATABASE_URL` pointed at Neon).
3. **Frontend** — put your Render URL in `frontend/.env.production`, push to `main`.
   The Actions workflow builds and deploys to Pages. Enable Pages with source
   "GitHub Actions" in repo settings.

The frontend uses `HashRouter` and a `base` path so it works under the Pages
subpath without server-side routing.

## Notes

- **Secrets**: `backend/.env` (IUCN token, DB URL, secret key) is git-ignored.
  `frontend/.env.production` holds only the public backend URL and is committed.
- **Map data**: IUCN provides country-level ranges, so map markers are plotted at
  country centroids — approximate by design, not precise sightings.
- **Model caveat**: the training data is heavily skewed toward "Decreasing", so the
  model predicts that for nearly everything. The detail view shows predicted vs.
  recorded trend so this is visible.

"""
Populate SpeciesLocation rows from IUCN assessment location data.

IUCN v4 gives country-level locations (ISO codes), not point coordinates, so each
species-country becomes one approximate marker at the country's centroid
(country_centroids.json). Approximate by design — good for a range overview, not
precise sightings.

Idempotent: clears existing rows for a species before reinserting.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
from app import app, db, Species, SpeciesLocation

load_dotenv()

IUCN_API_TOKEN = os.environ.get('IUCN_API_TOKEN', 'YOUR_V4_TOKEN_HERE')
BASE_URL = 'https://api.iucnredlist.org/api/v4'

# ISO 3166-1 alpha-2 -> [lat, lng] centroid
with open(os.path.join(os.path.dirname(__file__), 'country_centroids.json')) as f:
    CENTROIDS = json.load(f)


def get_headers():
    return {'Authorization': f'Bearer {IUCN_API_TOKEN}'}


def get_with_retry(url, max_retries=5):
    """GET with backoff on rate-limit (429) / transient 5xx. Returns Response or None.

    IUCN throttles sustained bursts, so we honor Retry-After and back off
    exponentially rather than silently treating a 429 as 'no data'.
    """
    delay = 2.0
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=get_headers(), timeout=20)
        except Exception as e:
            print(f"    request error ({e}); retrying in {delay:.0f}s")
            time.sleep(delay)
            delay *= 2
            continue

        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = float(resp.headers.get('Retry-After', delay))
            print(f"    HTTP {resp.status_code} (rate limit); waiting {wait:.0f}s")
            time.sleep(wait)
            delay *= 2
            continue
        # 4xx other than 429: won't succeed on retry.
        print(f"    HTTP {resp.status_code} — giving up on {url}")
        return None

    print(f"    exhausted retries for {url}")
    return None


def latest_assessment_id(taxon_id):
    """Resolve a species' latest assessment id from its SIS taxon id."""
    resp = get_with_retry(f"{BASE_URL}/taxa/sis/{taxon_id}")
    if resp is None:
        return None
    assessments = resp.json().get('assessments', [])
    latest = [a for a in assessments if a.get('latest')]
    chosen = latest[0] if latest else (assessments[0] if assessments else None)
    return chosen.get('assessment_id') if chosen else None


def fetch_locations(assessment_id):
    """Return list of (country_name, lat, lng) for an assessment's extant range."""
    resp = get_with_retry(f"{BASE_URL}/assessment/{assessment_id}")
    if resp is None:
        return []
    raw = resp.json().get('locations', [])

    out = []
    for loc in raw:
        # Skip locations where the species is no longer present.
        if loc.get('presence') not in (None, 'Extant', 'Probably Extant'):
            continue
        code = loc.get('code')
        centroid = CENTROIDS.get(code)
        if not centroid:
            continue
        name = (loc.get('description') or {}).get('en') or code
        out.append((name, centroid[0], centroid[1]))
    return out


def populate():
    print("=" * 60)
    print("POPULATING SPECIES LOCATIONS")
    print("=" * 60)

    if IUCN_API_TOKEN == 'YOUR_V4_TOKEN_HERE':
        print("\nERROR: Set IUCN_API_TOKEN in .env first.")
        return

    with app.app_context():
        species_list = Species.query.all()
        print(f"\nSpecies to process: {len(species_list)}")

        total_markers = 0
        skipped_no_taxon = 0

        for i, sp in enumerate(species_list, 1):
            print(f"\n[{i}/{len(species_list)}] {sp.scientific_name}")

            # Skip species that already have locations (resumable / incremental).
            if SpeciesLocation.query.filter_by(species_id=sp.id).first():
                continue

            if not sp.taxon_id:
                print("  no taxon_id — skipping")
                skipped_no_taxon += 1
                continue

            assessment_id = latest_assessment_id(sp.taxon_id)
            time.sleep(0.3)
            if not assessment_id:
                print("  no assessment found — skipping")
                continue

            locations = fetch_locations(assessment_id)
            time.sleep(0.3)

            # Replace this species' locations so re-runs stay idempotent.
            SpeciesLocation.query.filter_by(species_id=sp.id).delete()

            for name, lat, lng in locations:
                db.session.add(SpeciesLocation(
                    species_id=sp.id, latitude=lat, longitude=lng, country=name,
                ))

            try:
                db.session.commit()
                total_markers += len(locations)
                print(f"  saved {len(locations)} location(s)")
            except Exception as e:
                db.session.rollback()
                print(f"  DB error: {e}")

        print("\n" + "=" * 60)
        print("DONE")
        print("=" * 60)
        print(f"Total markers: {total_markers}")
        print(f"Species skipped (no taxon_id): {skipped_no_taxon}")
        print(f"Locations in DB: {SpeciesLocation.query.count()}")


if __name__ == '__main__':
    print("\nStarting location population (a few minutes)...\n")
    try:
        populate()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

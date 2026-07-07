"""
Load Species Data from IUCN Red List API v4

Fetches species across conservation categories, pulling taxonomy AND population
trend from each assessment detail in a single pass. Paginates category listings,
retries on rate-limiting, and skips species already in the DB (resumable).
"""

import os
import time
import requests
from dotenv import load_dotenv
from app import app, db, Species
from sqlalchemy.exc import IntegrityError

load_dotenv()

IUCN_API_TOKEN = os.environ.get('IUCN_API_TOKEN', 'YOUR_V4_TOKEN_HERE')
BASE_URL = 'https://api.iucnredlist.org/api/v4'

# Categories to load and how many latest assessments to target for each.
# LC/NT are included so the trend labels aren't all "Decreasing" (threatened
# categories skew heavily to declining populations).
CATEGORIES = [
    ('CR', 'Critically Endangered', 190),
    ('EN', 'Endangered', 190),
    ('VU', 'Vulnerable', 190),
    ('NT', 'Near Threatened', 190),
    ('LC', 'Least Concern', 190),
]

MAX_PAGES = 20  # safety cap on pagination per category


def get_headers():
    return {'Authorization': f'Bearer {IUCN_API_TOKEN}'}


def get_with_retry(url, max_retries=5):
    """GET with backoff on rate-limit (429) / transient 5xx. Returns Response or None."""
    delay = 2.0
    for _ in range(max_retries):
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
        print(f"    HTTP {resp.status_code} — giving up on {url}")
        return None

    print(f"    exhausted retries for {url}")
    return None


def fetch_category_assessments(category, target):
    """Paginate a category listing, collecting up to `target` latest assessments."""
    print(f"\nFetching {category} (target {target})...")
    collected = []
    page = 1
    while len(collected) < target and page <= MAX_PAGES:
        resp = get_with_retry(f"{BASE_URL}/red_list_categories/{category}?page={page}")
        if resp is None:
            break
        assessments = resp.json().get('assessments', [])
        if not assessments:
            break  # ran out of pages
        latest = [a for a in assessments if a.get('latest')]
        collected.extend(latest)
        print(f"  page {page}: +{len(latest)} latest (total {len(collected)})")
        page += 1
        time.sleep(0.3)

    return collected[:target]


def get_assessment_details(assessment_id):
    resp = get_with_retry(f"{BASE_URL}/assessment/{assessment_id}")
    return resp.json() if resp else None


def extract_trend(details):
    """Population trend from the assessment's top-level population_trend field."""
    pt = details.get('population_trend')
    if isinstance(pt, dict):
        name = (pt.get('description') or {}).get('en')
        if name:
            return name
    return 'Unknown'


def save_species(assessment, details):
    """Insert one species from its assessment summary + detail. Returns Species or None."""
    scientific_name = assessment.get('taxon_scientific_name')
    if not scientific_name:
        return None

    if Species.query.filter_by(scientific_name=scientific_name).first():
        return None  # already loaded

    taxon = (details or {}).get('taxon', {})
    common_name = None
    for cn in taxon.get('common_names', []) or []:
        if cn.get('language') == 'eng':
            common_name = cn.get('name')
            if cn.get('main'):
                break

    species = Species(
        taxon_id=assessment.get('sis_taxon_id'),
        scientific_name=scientific_name,
        common_name=common_name,
        kingdom=taxon.get('kingdom_name'),
        phylum=taxon.get('phylum_name'),
        class_name=taxon.get('class_name'),
        order=taxon.get('order_name'),
        family=taxon.get('family_name'),
        category=assessment.get('red_list_category_code'),
        population_trend=extract_trend(details or {}),
    )

    try:
        db.session.add(species)
        db.session.commit()
        return species
    except IntegrityError:
        db.session.rollback()
        return None
    except Exception as e:
        db.session.rollback()
        print(f"    save error: {e}")
        return None


def load_species_data():
    print("=" * 60)
    print("WILDLIFE CONSERVATION TRACKER - IUCN v4 DATA LOADER")
    print("=" * 60)

    if IUCN_API_TOKEN == 'YOUR_V4_TOKEN_HERE':
        print("\nERROR: Set IUCN_API_TOKEN in .env first.")
        return

    with app.app_context():
        total_new = 0

        for category, name, target in CATEGORIES:
            print(f"\n{'=' * 60}\nLoading {name} ({category})\n{'=' * 60}")
            assessments = fetch_category_assessments(category, target)

            for i, assessment in enumerate(assessments, 1):
                sci = assessment.get('taxon_scientific_name', 'Unknown')

                # Skip existing before spending a detail call (resumable re-runs).
                if Species.query.filter_by(scientific_name=sci).first():
                    continue

                details = get_assessment_details(assessment.get('assessment_id'))
                time.sleep(0.3)

                species = save_species(assessment, details)
                if species:
                    total_new += 1
                    if total_new % 25 == 0:
                        print(f"  ...{total_new} new species saved so far")

            print(f"  {category} done")

        # Summary
        print("\n" + "=" * 60)
        print("DATA LOADING COMPLETE")
        print("=" * 60)
        print(f"New species this run: {total_new}")
        print(f"Database total: {Species.query.count()}")

        print("\nTrend breakdown:")
        for trend in ['Increasing', 'Stable', 'Decreasing', 'Unknown']:
            print(f"  {trend}: {Species.query.filter_by(population_trend=trend).count()}")

        print("\nCategory breakdown:")
        for cat, _, _ in CATEGORIES:
            print(f"  {cat}: {Species.query.filter_by(category=cat).count()}")
        print("=" * 60)


if __name__ == '__main__':
    print("\nStarting IUCN v4 data load (this takes a while)...\n")
    try:
        load_species_data()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        with app.app_context():
            print(f"Saved so far: {Species.query.count()} species")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

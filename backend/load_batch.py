"""
Incrementally grow the species dataset one batch at a time, then retrain.

Run this manually whenever you want more data. Each run adds a bounded batch of
new species per category (so no single run marathons or over-hammers the IUCN
API), up to a per-category cap, keeping categories balanced. Then it retrains the
model on the enlarged set.

Design notes:
- Balanced growth: each run tops up every category by the same batch size until
  each reaches CAP_PER_CATEGORY (~5000 species total across 5 categories).
- Resumable: species already in the DB are skipped without spending a detail call.
- No feedback loop: retraining here uses only real IUCN-labeled trends. Unlike
  train_model.py it does NOT overwrite "Unknown" species with predictions, so the
  model never trains on its own guesses as it grows.

Usage:
    python load_batch.py                     # add a batch (default 60/category) + retrain
    python load_batch.py --per-category 100  # bigger batch this run
    python load_batch.py --with-locations    # also backfill map locations for new species
    python load_batch.py --no-train          # just load (retrain later)
"""

import argparse
import time

from app import app, db, Species
import load_species_data as loader
import train_model as trainer

CAP_PER_CATEGORY = 1000  # ~5000 species total across CR/EN/VU/NT/LC


def run_batch(per_category):
    """Top up each category by up to `per_category` new species (respecting the cap)."""
    added_total = 0
    with app.app_context():
        for code, name, _ in loader.CATEGORIES:
            have = Species.query.filter_by(category=code).count()
            room = min(per_category, CAP_PER_CATEGORY - have)
            if room <= 0:
                print(f"{code}: full ({have}/{CAP_PER_CATEGORY}) — skipping")
                continue

            # Page far enough to reach unseen species (we already have `have`).
            assessments = loader.fetch_category_assessments(code, have + room)

            added = 0
            for a in assessments:
                if added >= room:
                    break
                sci = a.get('taxon_scientific_name')
                if not sci or Species.query.filter_by(scientific_name=sci).first():
                    continue  # missing name or already loaded — no detail call spent
                details = loader.get_assessment_details(a.get('assessment_id'))
                time.sleep(0.3)
                if loader.save_species(a, details):
                    added += 1

            print(f"{code}: +{added} new (now {have + added}/{CAP_PER_CATEGORY})")
            added_total += added

    return added_total


def retrain():
    """Train + save on real-labeled data only (no predict-and-overwrite step)."""
    print("\n" + "=" * 60)
    print("RETRAINING (real labels only)")
    print("=" * 60)
    df = trainer.load_data_from_database()
    X, y, _X_unlabeled, _unlabeled_df = trainer.prepare_features(df)
    if X is None:
        print("Not enough labeled data to train — skipping retrain.")
        return
    model = trainer.train_model(X, y)
    trainer.save_model_and_encoders(model)


def main():
    parser = argparse.ArgumentParser(description="Grow the dataset by one batch, then retrain.")
    parser.add_argument('--per-category', type=int, default=60,
                        help='new species to add per category this run (default 60)')
    parser.add_argument('--with-locations', action='store_true',
                        help='also backfill map locations for newly added species')
    parser.add_argument('--no-train', action='store_true',
                        help='skip retraining (just load)')
    args = parser.parse_args()

    if loader.IUCN_API_TOKEN == 'YOUR_V4_TOKEN_HERE':
        print("ERROR: Set IUCN_API_TOKEN in .env first.")
        return

    with app.app_context():
        before = Species.query.count()
    print(f"Starting batch. Current species: {before}\n")

    added = run_batch(args.per_category)
    print(f"\nAdded this run: {added}")

    if added and args.with_locations:
        import populate_locations
        populate_locations.populate()  # incremental: skips species that already have locations

    if not args.no_train:
        if added:
            retrain()
        else:
            print("No new species — nothing to retrain.")

    with app.app_context():
        after = Species.query.count()
        print(f"\nDone. Species: {before} -> {after}")
        print("Per-category:")
        for code, _, _ in loader.CATEGORIES:
            n = Species.query.filter_by(category=code).count()
            print(f"  {code}: {n}/{CAP_PER_CATEGORY}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")

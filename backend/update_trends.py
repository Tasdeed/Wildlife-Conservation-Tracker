"""
Update Population Trends for Existing Species
Uses the population_trends endpoint to get actual trends
"""

import requests
import time
from app import app, db, Species

# REPLACE WITH YOUR ACTUAL V4 TOKEN
IUCN_API_TOKEN = 'hfhE16kGi1sJysee2BpSqT4erTDN2y3JeFw5'

BASE_URL = 'https://api.iucnredlist.org/api/v4'

# Population trend codes
TREND_CODES = {
    '0': 'Increasing',
    '1': 'Decreasing',
    '2': 'Stable',
    '3': 'Unknown'
}

def get_headers():
    return {'Authorization': f'Bearer {IUCN_API_TOKEN}'}

def fetch_species_by_trend(trend_code, max_results=300):
    """Fetch species with a specific population trend"""
    trend_name = TREND_CODES.get(trend_code, 'Unknown')
    print(f"\nFetching species with {trend_name} populations...")
    
    url = f"{BASE_URL}/population_trends/{trend_code}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            assessments = data.get('assessments', [])
            
            # Filter for latest only
            latest = [a for a in assessments if a.get('latest') == True]
            latest = latest[:max_results]
            
            print(f"  ✓ Found {len(latest)} species")
            return latest, trend_name
        else:
            print(f"  ❌ Error {response.status_code}")
            return [], trend_name
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return [], trend_name

def update_population_trends():
    """Update population trends for species in database"""
    
    print("=" * 60)
    print("UPDATING POPULATION TRENDS")
    print("=" * 60)
    
    if IUCN_API_TOKEN == 'YOUR_V4_TOKEN_HERE':
        print("\n❌ ERROR: Please add your API token!")
        return
    
    with app.app_context():
        # Check current state
        total = Species.query.count()
        unknown_count = Species.query.filter_by(population_trend='Unknown').count()
        
        print(f"\nCurrent state:")
        print(f"  Total species: {total}")
        print(f"  Unknown trends: {unknown_count}")
        
        if unknown_count == 0:
            print("\n✓ All species already have population trends!")
            return
        
        print(f"\nWill update {unknown_count} species...")
        
        updated_count = 0
        
        # Fetch each trend type
        for trend_code in ['0', '1', '2']:  # Skip '3' (Unknown)
            assessments, trend_name = fetch_species_by_trend(trend_code, max_results=300)
            
            print(f"\nProcessing {trend_name} species...")
            
            for i, assessment in enumerate(assessments, 1):
                scientific_name = assessment.get('taxon_scientific_name')
                
                if not scientific_name:
                    continue
                
                # Find in database
                species = Species.query.filter_by(scientific_name=scientific_name).first()
                
                if species:
                    old_trend = species.population_trend
                    species.population_trend = trend_name
                    
                    try:
                        db.session.commit()
                        updated_count += 1
                        
                        if i % 50 == 0:
                            print(f"  Updated {i}/{len(assessments)}...")
                    except Exception as e:
                        db.session.rollback()
                        print(f"  Error updating {scientific_name}: {e}")
                
                time.sleep(0.2)  # Rate limiting
            
            print(f"  ✓ Processed {len(assessments)} {trend_name} species")
            time.sleep(1)
        
        # Final summary
        print("\n" + "=" * 60)
        print("UPDATE COMPLETE!")
        print("=" * 60)
        print(f"Updated: {updated_count} species")
        
        # Show new breakdown
        print("\nNew Population Trend Breakdown:")
        for trend in ['Increasing', 'Stable', 'Decreasing', 'Unknown']:
            count = Species.query.filter_by(population_trend=trend).count()
            print(f"  {trend}: {count}")
        
        print("=" * 60)

if __name__ == '__main__':
    print("\nStarting population trend update...")
    print("This will take 5-10 minutes.\n")
    
    try:
        update_population_trends()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
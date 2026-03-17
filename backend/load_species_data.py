"""
Load Species Data from IUCN Red List API v4
WORKING VERSION - Correctly parses v4 API responses
"""

import requests
import time
from app import app, db, Species
from sqlalchemy.exc import IntegrityError

# REPLACE WITH YOUR ACTUAL V4 TOKEN
IUCN_API_TOKEN = 'hfhE16kGi1sJysee2BpSqT4erTDN2y3JeFw5'

BASE_URL = 'https://api.iucnredlist.org/api/v4'

# Population trend code mapping
POPULATION_TRENDS = {
    '0': 'Increasing',
    '1': 'Decreasing',
    '2': 'Stable',
    '3': 'Unknown'
}

def get_headers():
    """Return auth headers"""
    return {'Authorization': f'Bearer {IUCN_API_TOKEN}'}

def fetch_species_by_category(category, max_results=200):
    """Fetch species from a Red List category (CR, EN, VU)"""
    print(f"\nFetching {category} species...")
    
    url = f"{BASE_URL}/red_list_categories/{category}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Data is in 'assessments' key
            assessments = data.get('assessments', [])
            
            # Filter for latest assessments only
            latest_assessments = [a for a in assessments if a.get('latest') == True]
            
            # Limit results
            latest_assessments = latest_assessments[:max_results]
            
            print(f"  ✓ Total assessments: {len(assessments)}")
            print(f"  ✓ Latest assessments: {len(latest_assessments)}")
            
            return latest_assessments
        else:
            print(f"  ❌ Error {response.status_code}: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return []

def get_assessment_details(assessment_id):
    """Get detailed assessment data including population trend"""
    url = f"{BASE_URL}/assessment/{assessment_id}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    
    return None

def save_species_to_db(assessment_data, details=None):
    """Save species to database"""
    try:
        # Get scientific name from assessment
        scientific_name = assessment_data.get('taxon_scientific_name')
        
        if not scientific_name:
            return None
        
        # Check if exists
        existing = Species.query.filter_by(scientific_name=scientific_name).first()
        if existing:
            return existing
        
        # Get population trend from details if available
        population_trend = 'Unknown'
        if details and 'assessment' in details:
            assessment_info = details['assessment']
            trend_code = assessment_info.get('population_trend_code')
            if trend_code:
                population_trend = POPULATION_TRENDS.get(str(trend_code), 'Unknown')
        
        # Get taxonomy from details or use None
        if details and 'taxon' in details:
            taxon = details['taxon']
            kingdom = taxon.get('kingdom_name')
            phylum = taxon.get('phylum_name')
            class_name = taxon.get('class_name')
            order = taxon.get('order_name')
            family = taxon.get('family_name')
            
            # Get common name
            common_names = taxon.get('common_names', [])
            common_name = None
            if common_names:
                # Try to find main common name
                for cn in common_names:
                    if cn.get('main') == True and cn.get('language') == 'eng':
                        common_name = cn.get('name')
                        break
                # If no main, just use first English one
                if not common_name:
                    for cn in common_names:
                        if cn.get('language') == 'eng':
                            common_name = cn.get('name')
                            break
        else:
            kingdom = phylum = class_name = order = family = common_name = None
        
        # Create species
        species = Species(
            taxon_id=assessment_data.get('sis_taxon_id'),
            scientific_name=scientific_name,
            common_name=common_name,
            kingdom=kingdom,
            phylum=phylum,
            class_name=class_name,
            order=order,
            family=family,
            category=assessment_data.get('red_list_category_code'),
            population_trend=population_trend
        )
        
        db.session.add(species)
        db.session.commit()
        
        return species
    
    except IntegrityError:
        db.session.rollback()
        return None
    except Exception as e:
        db.session.rollback()
        print(f"    Error saving: {e}")
        return None

def load_species_data():
    """Main function to load species data"""
    
    print("=" * 60)
    print("WILDLIFE CONSERVATION TRACKER - IUCN v4 DATA LOADER")
    print("=" * 60)
    
    if IUCN_API_TOKEN == 'YOUR_V4_TOKEN_HERE':
        print("\n❌ ERROR: Please set your IUCN API token!")
        return
    
    # Test connection
    print("\nTesting API connection...")
    url = f"{BASE_URL}/information/api_version"
    response = requests.get(url, headers=get_headers(), timeout=10)
    
    if response.status_code != 200:
        print(f"❌ API connection failed: {response.status_code}")
        return
    
    print(f"✓ Connected to IUCN API {response.json().get('api_version')}")
    
    with app.app_context():
        categories = [
            ('CR', 'Critically Endangered', 200),
            ('EN', 'Endangered', 200),
            ('VU', 'Vulnerable', 200)
        ]
        
        total_species = 0
        
        for category, name, max_results in categories:
            print(f"\n{'=' * 60}")
            print(f"Loading {name} ({category}) species")
            print('=' * 60)
            
            # Fetch species list
            assessments = fetch_species_by_category(category, max_results)
            
            # Save each species
            for i, assessment in enumerate(assessments, 1):
                scientific_name = assessment.get('taxon_scientific_name', 'Unknown')
                assessment_id = assessment.get('assessment_id')
                
                print(f"\n[{i}/{len(assessments)}] {scientific_name}")
                
                # Get detailed assessment (for first 100 to save time)
                details = None
                if i <= 100:
                    print(f"  Fetching details...")
                    details = get_assessment_details(assessment_id)
                    time.sleep(0.3)
                
                # Save to database
                species_obj = save_species_to_db(assessment, details)
                
                if species_obj:
                    total_species += 1
                    trend = species_obj.population_trend or 'Unknown'
                    print(f"  ✓ Saved (ID: {species_obj.id}, Trend: {trend})")
                else:
                    print(f"  ⚠ Skipped (duplicate)")
                
                # Progress update
                if i % 25 == 0:
                    print(f"\n--- Progress: {i}/{len(assessments)} ---")
                    print(f"--- Total saved: {total_species} ---")
                
                time.sleep(0.4)  # Rate limiting
        
        # Final summary
        print("\n" + "=" * 60)
        print("DATA LOADING COMPLETE!")
        print("=" * 60)
        print(f"Total species saved: {total_species}")
        print(f"Database total: {Species.query.count()}")
        
        # Population trend breakdown
        print("\nPopulation Trend Breakdown:")
        for trend in ['Increasing', 'Stable', 'Decreasing', 'Unknown']:
            count = Species.query.filter_by(population_trend=trend).count()
            print(f"  {trend}: {count}")
        
        # Category breakdown
        print("\nCategory Breakdown:")
        for cat in ['CR', 'EN', 'VU']:
            count = Species.query.filter_by(category=cat).count()
            print(f"  {cat}: {count}")
        
        print("=" * 60)

if __name__ == '__main__':
    print("\nStarting IUCN v4 data load...")
    print("This will take 30-50 minutes.")
    print("Press Ctrl+C to cancel.\n")
    
    try:
        load_species_data()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        with app.app_context():
            print(f"Saved: {Species.query.count()} species")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
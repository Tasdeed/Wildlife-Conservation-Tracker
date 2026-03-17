"""
Test ML Prediction API Endpoints
Run this after starting Flask server (python app.py)
"""

import requests
import json

BASE_URL = 'http://localhost:5001'

def test_model_stats():
    """Test model statistics endpoint"""
    print("\n" + "=" * 60)
    print("TEST 1: Model Statistics")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/model/stats"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print("\nResponse:")
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200:
            print("\n✅ Model stats endpoint working!")
        else:
            print("\n❌ Error getting model stats")
    except Exception as e:
        print(f"\n❌ Exception: {e}")

def test_prediction(species_id=1):
    """Test prediction endpoint for a specific species"""
    print("\n" + "=" * 60)
    print(f"TEST 2: Predict Species {species_id}")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/predict/{species_id}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print("\nResponse:")
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200:
            print(f"\n✅ Prediction for {data.get('scientific_name')}:")
            print(f"   Predicted Trend: {data.get('predicted_trend')}")
            print(f"   Confidence: {data.get('confidence'):.2%}")
        else:
            print("\n❌ Error getting prediction")
    except Exception as e:
        print(f"\n❌ Exception: {e}")

def test_get_all_species():
    """Test getting all species"""
    print("\n" + "=" * 60)
    print("TEST 3: Get All Species")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/species?limit=5"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Total species returned: {data.get('count')}")
        
        if data.get('species'):
            print("\nFirst species:")
            first = data['species'][0]
            print(f"  ID: {first['id']}")
            print(f"  Name: {first['scientific_name']}")
            print(f"  Category: {first['category']}")
            print(f"  Population Trend: {first['population_trend']}")
            
            print("\n✅ Species endpoint working!")
        else:
            print("\n❌ No species returned")
    except Exception as e:
        print(f"\n❌ Exception: {e}")

def test_filter_by_trend():
    """Test filtering species by population trend"""
    print("\n" + "=" * 60)
    print("TEST 4: Filter by Decreasing Population")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/species?trend=Decreasing&limit=5"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Decreasing species returned: {data.get('count')}")
        
        if data.get('species'):
            print("\nSample species with decreasing populations:")
            for sp in data['species'][:3]:
                print(f"  - {sp['scientific_name']} ({sp['category']})")
            
            print("\n✅ Filtering working!")
        else:
            print("\n❌ No species returned")
    except Exception as e:
        print(f"\n❌ Exception: {e}")

def main():
    print("=" * 60)
    print("WILDLIFE CONSERVATION TRACKER - API TESTS")
    print("=" * 60)
    print("\nMake sure Flask is running on http://localhost:5001")
    print("Run: python app.py")
    
    input("\nPress Enter to start tests...")
    
    # Run all tests
    test_model_stats()
    test_prediction(species_id=1)
    test_get_all_species()
    test_filter_by_trend()
    
    # Test a few more predictions
    print("\n" + "=" * 60)
    print("TEST 5: Multiple Predictions")
    print("=" * 60)
    
    for species_id in [2, 5, 10]:
        test_prediction(species_id)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
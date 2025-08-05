"""
Test script for the Enhanced Equipment Prediction API
This script tests all endpoints to ensure they work correctly
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check: {health_data['status']}")
            print(f"   Model Loaded: {health_data['model_loaded']}")
            print(f"   Version: {health_data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_model_info_endpoint():
    """Test the model info endpoint"""
    print("\n🔍 Testing Model Info Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/model/info")
        if response.status_code == 200:
            model_info = response.json()
            print(f"✅ Model Info Retrieved")
            print(f"   Model Name: {model_info['model_name']}")
            print(f"   Model Type: {model_info['model_type']}")
            print(f"   Features: {len(model_info['features'])}")
            print(f"   Required Fields: {model_info['required_fields']}")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {str(e)}")
        return False

def test_single_prediction():
    """Test single equipment prediction"""
    print("\n🔍 Testing Single Prediction...")
    
    # Sample equipment data
    equipment_data = {
        "equipment_id": "TEST_001",
        "age_months": 24,
        "operating_temperature": 75.5,
        "vibration_level": 2.3,
        "power_consumption": 150.0,
        "humidity_level": 0.45,
        "dust_accumulation": 0.2,
        "performance_score": 0.85,
        "daily_usage_hours": 8.5
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/equipment/predict",
            json=equipment_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print(f"✅ Prediction Successful")
            print(f"   Equipment ID: {prediction['equipment_id']}")
            print(f"   Failure Probability: {prediction['failure_probability']:.3f}")
            print(f"   Risk Level: {prediction['risk_level']}")
            print(f"   Confidence Score: {prediction['confidence_score']:.3f}")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return False

def test_batch_prediction():
    """Test batch equipment prediction"""
    print("\n🔍 Testing Batch Prediction...")
    
    # Sample batch data
    equipment_list = [
        {
            "equipment_id": "BATCH_001",
            "age_months": 12,
            "operating_temperature": 70.0,
            "vibration_level": 1.5,
            "power_consumption": 120.0
        },
        {
            "equipment_id": "BATCH_002",
            "age_months": 36,
            "operating_temperature": 85.0,
            "vibration_level": 4.2,
            "power_consumption": 180.0
        },
        {
            "equipment_id": "BATCH_003",
            "age_months": 6,
            "operating_temperature": 65.0,
            "vibration_level": 1.0,
            "power_consumption": 100.0
        }
    ]
    
    batch_data = {"equipment_list": equipment_list}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/equipment/batch-predict",
            json=batch_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"✅ Batch Prediction Successful")
            print(f"   Total Requested: {batch_result['total_requested']}")
            print(f"   Total Processed: {batch_result['total_processed']}")
            print(f"   Total Errors: {batch_result['total_errors']}")
            
            if batch_result['predictions']:
                print("   Predictions:")
                for pred in batch_result['predictions']:
                    print(f"     {pred['equipment_id']}: {pred['risk_level']} ({pred['failure_probability']:.3f})")
            
            return True
        else:
            print(f"❌ Batch prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Batch prediction error: {str(e)}")
        return False

def test_error_handling():
    """Test API error handling"""
    print("\n🔍 Testing Error Handling...")
    
    # Test with missing required fields
    invalid_data = {
        "equipment_id": "ERROR_TEST",
        "age_months": 12
        # Missing required fields
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/equipment/predict",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            error_response = response.json()
            print(f"✅ Error Handling Works")
            print(f"   Error Message: {error_response.get('error', 'No error message')}")
            return True
        else:
            print(f"❌ Expected 400 error, got: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Model Info", test_model_info_endpoint),
        ("Single Prediction", test_single_prediction),
        ("Batch Prediction", test_batch_prediction),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! API is ready for .NET integration.")
    else:
        print("⚠️  Some tests failed. Please check the API setup.")

if __name__ == "__main__":
    main()

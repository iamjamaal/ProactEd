"""
API Endpoint Tests
================

Tests for REST API endpoints:
- Endpoint availability and response codes
- Request/response validation
- Error handling
- Performance testing
- Authentication testing
"""

import pytest
import json
import time
import sys
import os
from unittest.mock import patch, Mock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = Mock()

class TestAPIEndpoints:
    """Test REST API endpoints"""
    
    BASE_URL = "http://localhost:5000"
    API_TIMEOUT = 5.0
    
    @pytest.fixture
    def api_client(self):
        """Mock API client for testing"""
        if not HAS_REQUESTS:
            return Mock()
        return requests.Session()
    
    def test_health_check_endpoint(self, api_client):
        """Test API health check endpoint"""
        if HAS_REQUESTS:
            try:
                response = api_client.get(f"{self.BASE_URL}/health", timeout=self.API_TIMEOUT)
                assert response.status_code == 200
                
                health_data = response.json()
                assert 'status' in health_data
                assert health_data['status'] == 'healthy'
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_predict_endpoint(self, api_client, sample_data):
        """Test prediction endpoint"""
        if HAS_REQUESTS:
            try:
                # Convert sample data to JSON
                payload = sample_data.to_dict('records')
                
                response = api_client.post(
                    f"{self.BASE_URL}/predict",
                    json=payload,
                    timeout=self.API_TIMEOUT
                )
                
                if response.status_code == 200:
                    predictions = response.json()
                    
                    assert 'predictions' in predictions
                    assert len(predictions['predictions']) > 0
                    
                    # Validate prediction structure
                    for pred in predictions['predictions']:
                        assert 'equipment_id' in pred
                        assert 'failure_probability' in pred
                        assert 0 <= pred['failure_probability'] <= 1
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_api_error_handling(self, api_client):
        """Test API error handling with invalid data"""
        if HAS_REQUESTS:
            try:
                # Test with invalid JSON
                response = api_client.post(
                    f"{self.BASE_URL}/predict",
                    data="invalid json",
                    timeout=self.API_TIMEOUT
                )
                
                assert response.status_code in [400, 422]  # Bad request or validation error
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_api_response_time(self, api_client, sample_data):
        """Test API response time"""
        from tests.conftest import TestConfig
        
        if HAS_REQUESTS:
            try:
                payload = sample_data.head(10).to_dict('records')  # Small sample for speed
                
                start_time = time.time()
                response = api_client.post(
                    f"{self.BASE_URL}/predict",
                    json=payload,
                    timeout=self.API_TIMEOUT
                )
                end_time = time.time()
                
                response_time = end_time - start_time
                assert response_time <= TestConfig.MAX_API_RESPONSE_TIME
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_api_data_validation(self, api_client):
        """Test API input validation"""
        if HAS_REQUESTS:
            try:
                # Test with missing required fields
                invalid_payload = [{"equipment_id": "TEST-001"}]  # Missing other required fields
                
                response = api_client.post(
                    f"{self.BASE_URL}/predict",
                    json=invalid_payload,
                    timeout=self.API_TIMEOUT
                )
                
                # Should return error for missing fields
                assert response.status_code in [400, 422]
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")

class TestAPIIntegration:
    """Test API integration scenarios"""
    
    def test_batch_prediction_limits(self, api_client):
        """Test batch prediction size limits"""
        if HAS_REQUESTS:
            try:
                # Test with large batch
                large_payload = [{"equipment_id": f"TEST-{i:03d}"} for i in range(1000)]
                
                response = api_client.post(
                    f"{self.BASE_URL}/predict",
                    json=large_payload,
                    timeout=30.0  # Longer timeout for large batch
                )
                
                # Should handle or reject appropriately
                assert response.status_code in [200, 413, 422]  # OK, Too Large, or Validation Error
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_concurrent_requests(self, api_client, sample_data):
        """Test handling of concurrent requests"""
        import threading
        
        if HAS_REQUESTS:
            try:
                results = []
                errors = []
                
                def make_request():
                    try:
                        payload = sample_data.head(5).to_dict('records')
                        response = api_client.post(
                            f"{self.BASE_URL}/predict",
                            json=payload,
                            timeout=self.API_TIMEOUT
                        )
                        results.append(response.status_code)
                    except Exception as e:
                        errors.append(e)
                
                # Create multiple threads
                threads = []
                for _ in range(5):
                    thread = threading.Thread(target=make_request)
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads
                for thread in threads:
                    thread.join()
                
                # Check results
                if results:
                    assert all(status == 200 for status in results)
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")

class TestAPIDocumentation:
    """Test API documentation and OpenAPI compliance"""
    
    def test_openapi_spec_available(self, api_client):
        """Test that OpenAPI specification is available"""
        if HAS_REQUESTS:
            try:
                response = api_client.get(f"{self.BASE_URL}/swagger.json", timeout=self.API_TIMEOUT)
                
                if response.status_code == 200:
                    spec = response.json()
                    
                    assert 'openapi' in spec or 'swagger' in spec
                    assert 'paths' in spec
                    assert 'info' in spec
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")
    
    def test_api_version_info(self, api_client):
        """Test API version information"""
        if HAS_REQUESTS:
            try:
                response = api_client.get(f"{self.BASE_URL}/version", timeout=self.API_TIMEOUT)
                
                if response.status_code == 200:
                    version_info = response.json()
                    
                    assert 'version' in version_info
                    assert 'build_date' in version_info
                
            except requests.ConnectionError:
                pytest.skip("API server not running")
        else:
            pytest.skip("requests library not available")

# Mock API tests for when server is not running
class TestAPIMock:
    """Mock API tests that don't require a running server"""
    
    def test_api_module_import(self):
        """Test that API module can be imported"""
        try:
            import equipment_api
            assert hasattr(equipment_api, 'app')
        except ImportError:
            pytest.skip("equipment_api module not available")
    
    def test_api_configuration(self):
        """Test API configuration"""
        try:
            import equipment_api
            
            # Check that Flask app is configured
            if hasattr(equipment_api, 'app'):
                app = equipment_api.app
                assert app is not None
                
        except ImportError:
            pytest.skip("equipment_api module not available")

if __name__ == "__main__":
    pytest.main([__file__, '-v'])

"""
Equipment Failure Prediction System - Unit Tests
=======================

Comprehensive test suite for all system components.

Test Categories:
- Model Performance Tests
- Data Processing Tests  
- API Endpoint Tests
- Dashboard Component Tests
- Integration Tests
- Business Logic Tests

Usage:
    python -m pytest tests/
    python -m pytest tests/test_models.py -v
    python -m pytest tests/ --cov=. --cov-report=html
"""

import pytest
import pandas as pd
import numpy as np
import pickle
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test Configuration
TEST_DATA_SIZE = 100
RANDOM_SEED = 42
TOLERANCE = 1e-4

class TestConfig:
    """Test configuration and constants"""
    
    # Model performance thresholds
    MIN_R2_SCORE = 0.5
    MAX_PREDICTION_TIME = 1.0  # seconds
    MIN_ACCURACY = 0.4
    
    # API response times
    MAX_API_RESPONSE_TIME = 2.0  # seconds
    
    # Data quality thresholds
    MAX_MISSING_DATA_PERCENT = 5.0
    MIN_DATA_COMPLETENESS = 0.95
    
    # Business logic thresholds
    MIN_COST_SAVINGS = 1000000  # $1M minimum annual savings
    MAX_FALSE_POSITIVE_RATE = 0.1
    
    @staticmethod
    def create_sample_equipment_data(size=TEST_DATA_SIZE):
        """Create sample equipment data for testing"""
        np.random.seed(RANDOM_SEED)
        
        data = {
            'equipment_id': [f'EQ-{i:03d}' for i in range(size)],
            'equipment_type': np.random.choice(['Projector', 'Air Conditioner', 'Podium'], size),
            'age_months': np.random.randint(6, 120, size),
            'last_maintenance_days': np.random.randint(0, 365, size),
            'operating_hours': np.random.randint(1000, 8760, size),
            'temperature': np.random.normal(75, 15, size),
            'vibration': np.random.exponential(2, size),
            'pressure': np.random.normal(14.7, 2, size),
            'power_consumption': np.random.normal(1500, 500, size),
            'failure_probability': np.random.beta(2, 8, size),  # Most equipment low risk
            'utilization_rate': np.random.uniform(0.3, 1.0, size),
            'maintenance_frequency': np.random.randint(1, 12, size),
            'environmental_conditions': np.random.choice(['Good', 'Fair', 'Poor'], size),
            'load_factor': np.random.uniform(0.4, 1.2, size),
            'efficiency_rating': np.random.uniform(0.7, 0.98, size)
        }
        
        return pd.DataFrame(data)
    
    @staticmethod
    def create_invalid_data():
        """Create invalid data for negative testing"""
        return pd.DataFrame({
            'equipment_id': ['INVALID'],
            'equipment_type': [None],
            'age_months': [-1],
            'temperature': [np.inf],
            'failure_probability': [1.5]  # Invalid probability > 1
        })

# Test Fixtures
@pytest.fixture
def sample_data():
    """Fixture providing sample equipment data"""
    return TestConfig.create_sample_equipment_data()

@pytest.fixture
def invalid_data():
    """Fixture providing invalid data for testing error handling"""
    return TestConfig.create_invalid_data()

@pytest.fixture
def mock_model_system():
    """Fixture providing a mock model system"""
    mock_model = Mock()
    mock_model.predict.return_value = np.random.beta(2, 8, TEST_DATA_SIZE)
    
    mock_system = {
        'model_info': {
            'model_object': mock_model,
            'features': ['age_months', 'temperature', 'vibration', 'pressure', 'power_consumption'],
            'optimal_threshold': 0.6,
            'performance_metrics': {
                'r2_score': 0.85,
                'accuracy': 0.82,
                'precision': 0.78,
                'recall': 0.85
            }
        },
        'business_impact': {
            'annual_savings': 5000000,
            'roi_percentage': 250.0,
            'cost_per_failure': 50000
        },
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'version': '1.0.0',
            'data_version': 'v1.0'
        }
    }
    return mock_system

def run_test_suite():
    """Run the complete test suite"""
    pytest.main([
        'tests/',
        '-v',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--tb=short'
    ])

if __name__ == "__main__":
    run_test_suite()

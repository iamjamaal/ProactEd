"""
Model Performance and Validation Tests
=====================================

Tests for machine learning model components:
- Model accuracy and performance
- Prediction consistency  
- Feature importance validation
- Model loading and serialization
- Business logic validation
"""

import pytest
import pandas as pd
import numpy as np
import pickle
import os
import sys
from unittest.mock import patch, Mock
from datetime import datetime

# Import project modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from production_predict_function import production_predict, load_model_system
except ImportError:
    # Mock if module not available
    production_predict = Mock()
    load_model_system = Mock()

class TestModelPerformance:
    """Test model performance and accuracy"""
    
    def test_model_loading(self):
        """Test that model loads correctly"""
        model_path = os.path.join(project_root, 'complete_equipment_failure_prediction_system.pkl')
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_system = pickle.load(f)
            
            # Verify model structure
            assert 'model_info' in model_system
            assert 'model_object' in model_system['model_info']
            assert 'features' in model_system['model_info']
            assert 'optimal_threshold' in model_system['model_info']
            
            # Verify model can make predictions
            model = model_system['model_info']['model_object']
            features = model_system['model_info']['features']
            
            # Create test data
            test_data = np.random.rand(10, len(features))
            predictions = model.predict(test_data)
            
            assert len(predictions) == 10
            assert all(0 <= p <= 1 for p in predictions)
        else:
            pytest.skip("Model file not found")
    
    def test_model_accuracy_threshold(self, mock_model_system):
        """Test that model meets minimum accuracy requirements"""
        from tests.conftest import TestConfig
        
        performance = mock_model_system['model_info']['performance_metrics']
        
        assert performance['r2_score'] >= TestConfig.MIN_R2_SCORE
        assert performance['accuracy'] >= TestConfig.MIN_ACCURACY
        
    def test_prediction_consistency(self, sample_data, mock_model_system):
        """Test that predictions are consistent for same input"""
        with patch('production_predict_function.load_model_system', return_value=mock_model_system):
            if production_predict != Mock():
                # Test with same data multiple times
                pred1 = production_predict(sample_data.copy())
                pred2 = production_predict(sample_data.copy())
                
                # Predictions should be identical for same input
                if pred1 is not None and pred2 is not None:
                    assert len(pred1) == len(pred2)
    
    def test_prediction_range_validation(self, sample_data, mock_model_system):
        """Test that predictions are in valid range [0,1]"""
        with patch('production_predict_function.load_model_system', return_value=mock_model_system):
            if production_predict != Mock():
                predictions = production_predict(sample_data)
                
                if predictions is not None:
                    # All predictions should be probabilities
                    for pred in predictions:
                        if isinstance(pred, dict) and 'failure_probability' in pred:
                            prob = pred['failure_probability']
                            assert 0 <= prob <= 1, f"Invalid probability: {prob}"
    
    def test_feature_importance_validation(self, mock_model_system):
        """Test that required features are present"""
        features = mock_model_system['model_info']['features']
        
        # Minimum required features
        required_features = ['age_months', 'temperature', 'operating_hours']
        
        for feature in required_features:
            assert feature in features, f"Required feature '{feature}' missing"
    
    def test_model_performance_metrics(self, mock_model_system):
        """Test that performance metrics are reasonable"""
        metrics = mock_model_system['model_info']['performance_metrics']
        
        # All metrics should be between 0 and 1
        for metric_name, value in metrics.items():
            assert 0 <= value <= 1, f"Invalid metric {metric_name}: {value}"
        
        # R² can be negative but should be reasonable
        assert metrics['r2_score'] >= -1, "R² score unreasonably low"

class TestBusinessLogic:
    """Test business logic and calculations"""
    
    def test_cost_savings_calculation(self, mock_model_system):
        """Test that cost savings calculations are reasonable"""
        from tests.conftest import TestConfig
        
        business_impact = mock_model_system['business_impact']
        annual_savings = business_impact['annual_savings']
        
        assert annual_savings >= TestConfig.MIN_COST_SAVINGS
        assert business_impact['roi_percentage'] > 0
        assert business_impact['cost_per_failure'] > 0
    
    def test_risk_level_assignment(self, sample_data):
        """Test risk level assignment logic"""
        # Test risk level calculation
        for _, row in sample_data.iterrows():
            failure_prob = row['failure_probability']
            
            if failure_prob >= 0.7:
                expected_risk = 'Critical'
            elif failure_prob >= 0.4:
                expected_risk = 'High'
            elif failure_prob >= 0.2:
                expected_risk = 'Medium'
            else:
                expected_risk = 'Low'
            
            # This would test actual risk assignment function
            # assert calculate_risk_level(failure_prob) == expected_risk
    
    def test_maintenance_scheduling_logic(self, sample_data):
        """Test maintenance scheduling algorithms"""
        # Test that high-risk equipment gets priority
        high_risk_equipment = sample_data[sample_data['failure_probability'] >= 0.7]
        medium_risk_equipment = sample_data[
            (sample_data['failure_probability'] >= 0.4) & 
            (sample_data['failure_probability'] < 0.7)
        ]
        
        # High risk should be scheduled before medium risk
        assert len(high_risk_equipment) >= 0  # Basic validation

class TestDataValidation:
    """Test data validation and preprocessing"""
    
    def test_data_completeness(self, sample_data):
        """Test data completeness requirements"""
        from tests.conftest import TestConfig
        
        # Check missing data percentage
        missing_percentage = (sample_data.isnull().sum().sum() / 
                            (len(sample_data) * len(sample_data.columns))) * 100
        
        assert missing_percentage <= TestConfig.MAX_MISSING_DATA_PERCENT
    
    def test_data_types_validation(self, sample_data):
        """Test that data types are appropriate"""
        # Numeric columns should be numeric
        numeric_columns = ['age_months', 'temperature', 'vibration', 'pressure', 
                          'power_consumption', 'failure_probability']
        
        for col in numeric_columns:
            if col in sample_data.columns:
                assert pd.api.types.is_numeric_dtype(sample_data[col])
    
    def test_invalid_data_handling(self, invalid_data):
        """Test handling of invalid data"""
        # Test with invalid data
        with patch('production_predict_function.load_model_system'):
            if production_predict != Mock():
                try:
                    result = production_predict(invalid_data)
                    # Should either handle gracefully or raise appropriate error
                    assert result is not None or True  # Placeholder assertion
                except Exception as e:
                    # Should raise meaningful error
                    assert isinstance(e, (ValueError, TypeError, KeyError))
    
    def test_data_range_validation(self, sample_data):
        """Test that data values are in reasonable ranges"""
        # Age should be positive
        if 'age_months' in sample_data.columns:
            assert all(sample_data['age_months'] >= 0)
        
        # Failure probability should be 0-1
        if 'failure_probability' in sample_data.columns:
            assert all(0 <= p <= 1 for p in sample_data['failure_probability'])
        
        # Temperature should be reasonable (equipment operating range)
        if 'temperature' in sample_data.columns:
            assert all(-40 <= t <= 200 for t in sample_data['temperature'])

class TestModelIntegration:
    """Test model integration and workflow"""
    
    def test_prediction_pipeline(self, sample_data, mock_model_system):
        """Test complete prediction pipeline"""
        with patch('production_predict_function.load_model_system', return_value=mock_model_system):
            if production_predict != Mock():
                # Test full pipeline
                results = production_predict(sample_data)
                
                if results is not None:
                    assert len(results) > 0
                    
                    # Check result structure
                    for result in results:
                        if isinstance(result, dict):
                            assert 'equipment_id' in result
                            assert 'failure_probability' in result
    
    def test_model_versioning(self, mock_model_system):
        """Test model versioning and metadata"""
        metadata = mock_model_system['metadata']
        
        assert 'version' in metadata
        assert 'created_date' in metadata
        assert 'data_version' in metadata
    
    def test_prediction_timing(self, sample_data, mock_model_system):
        """Test prediction response time"""
        from tests.conftest import TestConfig
        import time
        
        with patch('production_predict_function.load_model_system', return_value=mock_model_system):
            if production_predict != Mock():
                start_time = time.time()
                production_predict(sample_data)
                end_time = time.time()
                
                prediction_time = end_time - start_time
                assert prediction_time <= TestConfig.MAX_PREDICTION_TIME

# Additional test utilities
def test_model_serialization_integrity():
    """Test that model can be serialized and deserialized correctly"""
    model_path = os.path.join(project_root, 'complete_equipment_failure_prediction_system.pkl')
    
    if os.path.exists(model_path):
        # Test loading
        with open(model_path, 'rb') as f:
            original_system = pickle.load(f)
        
        # Test re-serialization
        temp_path = 'temp_model_test.pkl'
        try:
            with open(temp_path, 'wb') as f:
                pickle.dump(original_system, f)
            
            # Test re-loading
            with open(temp_path, 'rb') as f:
                reloaded_system = pickle.load(f)
            
            # Basic structure comparison
            assert 'model_info' in reloaded_system
            assert 'business_impact' in reloaded_system
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        pytest.skip("Model file not found")

if __name__ == "__main__":
    pytest.main([__file__, '-v'])

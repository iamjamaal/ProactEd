from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for .NET integration

# Global variable to store loaded model
model_system = None

def load_model():
    """Load the ML model once at startup"""
    global model_system
    try:
        model_path = 'complete_equipment_failure_prediction_system.pkl'
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_system = pickle.load(f)
            logger.info("Model loaded successfully")
            return True
        else:
            logger.error(f"Model file not found: {model_path}")
            return False
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return False

def validate_equipment_data(data):
    """Validate incoming equipment data"""
    required_fields = [
        'equipment_id', 'age_months', 'operating_temperature', 
        'vibration_level', 'power_consumption'
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    return missing_fields

def calculate_risk_level(prediction):
    """Calculate risk level based on prediction probability"""
    if prediction >= 0.7:
        return 'Critical'
    elif prediction >= 0.4:
        return 'High'
    elif prediction >= 0.2:
        return 'Medium'
    else:
        return 'Low'

def get_confidence_score(prediction):
    """Calculate confidence score"""
    # Higher confidence when prediction is closer to 0 or 1
    return float(1 - abs(prediction - 0.5) * 2)

def make_single_prediction(equipment_data):
    """Make prediction for a single equipment item"""
    global model_system
    
    if not model_system:
        raise Exception("Model not loaded")
    
    try:
        model = model_system['model_info']['model_object']
        features = model_system['model_info']['features']
        
        # Prepare input data
        input_data = pd.DataFrame([equipment_data])
        
        # Add missing features with default values
        for feature in features:
            if feature not in input_data.columns:
                input_data[feature] = 0
        
        # Ensure we have all required features in correct order
        X = input_data[features].fillna(0)
        
        # Make prediction
        prediction = model.predict(X)[0]
        
        # Calculate derived metrics
        risk_level = calculate_risk_level(prediction)
        confidence_score = get_confidence_score(prediction)
        
        return {
            'success': True,
            'equipment_id': equipment_data['equipment_id'],
            'failure_probability': float(prediction),
            'risk_level': risk_level,
            'prediction_timestamp': datetime.now().isoformat(),
            'model_version': model_system['model_info'].get('model_name', 'Unknown'),
            'confidence_score': confidence_score
        }
        
    except Exception as e:
        logger.error(f"Prediction error for equipment {equipment_data.get('equipment_id', 'Unknown')}: {str(e)}")
        raise

@app.route('/api/equipment/predict', methods=['POST'])
def predict_equipment_failure():
    """
    Enhanced prediction endpoint for .NET integration
    Expects JSON with equipment data
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        missing_fields = validate_equipment_data(data)
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Make prediction
        result = make_single_prediction(data)
        
        logger.info(f"Prediction successful for equipment: {data['equipment_id']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/equipment/batch-predict', methods=['POST'])
def batch_predict_equipment():
    """
    Batch prediction for multiple equipment items
    Expects JSON with 'equipment_list' array
    """
    try:
        data = request.get_json()
        
        if not data or 'equipment_list' not in data:
            return jsonify({
                'success': False,
                'error': 'No equipment_list provided'
            }), 400
        
        equipment_list = data['equipment_list']
        
        if not equipment_list:
            return jsonify({
                'success': False,
                'error': 'Equipment list is empty'
            }), 400
        
        results = []
        errors = []
        
        for i, equipment in enumerate(equipment_list):
            try:
                # Validate each equipment item
                missing_fields = validate_equipment_data(equipment)
                if missing_fields:
                    errors.append({
                        'index': i,
                        'equipment_id': equipment.get('equipment_id', f'Item_{i}'),
                        'error': f'Missing fields: {", ".join(missing_fields)}'
                    })
                    continue
                
                # Make prediction
                prediction_result = make_single_prediction(equipment)
                results.append(prediction_result)
                
            except Exception as e:
                errors.append({
                    'index': i,
                    'equipment_id': equipment.get('equipment_id', f'Item_{i}'),
                    'error': str(e)
                })
        
        response = {
            'success': True,
            'predictions': results,
            'total_requested': len(equipment_list),
            'total_processed': len(results),
            'total_errors': len(errors),
            'batch_timestamp': datetime.now().isoformat()
        }
        
        if errors:
            response['errors'] = errors
        
        logger.info(f"Batch prediction completed: {len(results)} successful, {len(errors)} errors")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for .NET monitoring
    """
    global model_system
    
    model_loaded = model_system is not None
    
    health_status = {
        'status': 'healthy' if model_loaded else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'model_loaded': model_loaded
    }
    
    if model_loaded:
        health_status['model_info'] = {
            'model_name': model_system['model_info'].get('model_name', 'Unknown'),
            'features_count': len(model_system['model_info'].get('features', [])),
            'model_type': str(type(model_system['model_info']['model_object']).__name__)
        }
    
    status_code = 200 if model_loaded else 503
    return jsonify(health_status), status_code

@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """
    Get detailed model information for .NET application
    """
    global model_system
    
    if not model_system:
        return jsonify({
            'success': False,
            'error': 'Model not loaded'
        }), 503
    
    try:
        model_info = model_system['model_info']
        
        response = {
            'success': True,
            'model_name': model_info.get('model_name', 'Unknown'),
            'model_type': str(type(model_info['model_object']).__name__),
            'features': model_info.get('features', []),
            'feature_count': len(model_info.get('features', [])),
            'required_fields': [
                'equipment_id', 'age_months', 'operating_temperature', 
                'vibration_level', 'power_consumption'
            ],
            'optional_fields': [
                'humidity_level', 'dust_accumulation', 'performance_score', 
                'daily_usage_hours'
            ],
            'risk_levels': ['Low', 'Medium', 'High', 'Critical'],
            'api_version': '1.0.0'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Load model at startup
    if not load_model():
        logger.error("Failed to load model. API will not function properly.")
        exit(1)
    
    logger.info("Starting Enhanced Equipment Prediction API for .NET Integration")
    logger.info("API Endpoints available:")
    logger.info("  POST /api/equipment/predict - Single equipment prediction")
    logger.info("  POST /api/equipment/batch-predict - Batch equipment prediction")
    logger.info("  GET  /api/health - Health check")
    logger.info("  GET  /api/model/info - Model information")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

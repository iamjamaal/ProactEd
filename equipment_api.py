
from flask import Flask, request, jsonify
import pandas as pd
import pickle
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load model on startup
def load_model():
    try:
        with open('complete_equipment_failure_prediction_system.pkl', 'rb') as f:
            system = pickle.load(f)
        logger.info("Model loaded successfully")
        return system
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

# Global model object
MODEL_SYSTEM = load_model()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': MODEL_SYSTEM is not None
    })

@app.route('/predict', methods=['POST'])
def predict_failure():
    """Predict equipment failure probability"""
    try:
        # Get data from request
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame([data])
        
        # Make predictions
        model = MODEL_SYSTEM['model_info']['model_object']
        features = MODEL_SYSTEM['model_info']['features']
        threshold = MODEL_SYSTEM['model_info']['optimal_threshold']
        
        # Ensure all features are present
        for feature in features:
            if feature not in df.columns:
                df[feature] = 0
        
        # Make predictions
        X = df[features].fillna(0)
        predictions = model.predict(X)
        
        # Format response
        results = []
        for i, pred in enumerate(predictions):
            urgency = 'critical' if pred >= 0.7 else 'high' if pred >= 0.4 else 'medium' if pred >= 0.2 else 'low'
            
            results.append({
                'equipment_id': df.index[i] if 'equipment_id' not in df.columns else df.iloc[i]['equipment_id'],
                'failure_probability': float(pred),
                'maintenance_urgency': urgency,
                'alert_required': bool(pred >= threshold),
                'prediction_timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'predictions': results,
            'model_info': {
                'model_name': MODEL_SYSTEM['model_info']['model_name'],
                'threshold': threshold
            }
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    """Batch prediction for multiple equipment"""
    try:
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            df = pd.read_csv(file)
        else:
            data = request.json
            df = pd.DataFrame(data)
        
        # Make predictions (same logic as single prediction)
        model = MODEL_SYSTEM['model_info']['model_object']
        features = MODEL_SYSTEM['model_info']['features']
        threshold = MODEL_SYSTEM['model_info']['optimal_threshold']
        
        for feature in features:
            if feature not in df.columns:
                df[feature] = 0
        
        X = df[features].fillna(0)
        predictions = model.predict(X)
        
        # Create results DataFrame
        results_df = df.copy() if 'equipment_id' in df.columns else df.reset_index()
        results_df['failure_probability'] = predictions
        results_df['maintenance_urgency'] = [
            'critical' if p >= 0.7 else 'high' if p >= 0.4 else 'medium' if p >= 0.2 else 'low'
            for p in predictions
        ]
        results_df['alert_required'] = predictions >= threshold
        
        return jsonify({
            'total_equipment': len(results_df),
            'alerts_generated': int(sum(predictions >= threshold)),
            'predictions': results_df.to_dict('records')
        })
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/model_info', methods=['GET'])
def get_model_info():
    """Get model information and performance metrics"""
    if MODEL_SYSTEM is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'model_name': MODEL_SYSTEM['model_info']['model_name'],
        'features_count': len(MODEL_SYSTEM['model_info']['features']),
        'optimal_threshold': MODEL_SYSTEM['model_info']['optimal_threshold'],
        'performance_metrics': MODEL_SYSTEM['model_info']['performance_metrics'],
        'business_parameters': MODEL_SYSTEM['business_parameters'],
        'last_updated': datetime.now().isoformat()
    })

@app.route('/maintenance_schedule', methods=['POST'])
def generate_maintenance_schedule():
    """Generate maintenance schedule for equipment"""
    try:
        data = request.json
        df = pd.DataFrame(data)
        
        # Make predictions
        model = MODEL_SYSTEM['model_info']['model_object']
        features = MODEL_SYSTEM['model_info']['features']
        threshold = MODEL_SYSTEM['model_info']['optimal_threshold']
        
        for feature in features:
            if feature not in df.columns:
                df[feature] = 0
        
        X = df[features].fillna(0)
        predictions = model.predict(X)
        
        # Filter high-risk equipment
        df['failure_probability'] = predictions
        high_risk = df[df['failure_probability'] >= threshold].copy()
        high_risk = high_risk.sort_values('failure_probability', ascending=False)
        
        # Generate schedule
        schedule = []
        for idx, equipment in high_risk.iterrows():
            priority = 1 if equipment['failure_probability'] >= 0.7 else 2 if equipment['failure_probability'] >= 0.4 else 3
            
            schedule.append({
                'equipment_id': idx,
                'failure_probability': float(equipment['failure_probability']),
                'priority': priority,
                'recommended_date': (datetime.now() + timedelta(days=1 if priority == 1 else 7 if priority == 2 else 30)).isoformat(),
                'estimated_cost': 500 if priority >= 2 else 2000  # From business parameters
            })
        
        return jsonify({
            'maintenance_schedule': schedule,
            'total_equipment': len(schedule),
            'estimated_total_cost': sum(item['estimated_cost'] for item in schedule)
        })
        
    except Exception as e:
        logger.error(f"Schedule generation error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


import pandas as pd
import pickle
import numpy as np

def production_predict(equipment_data):
    """
    Production-ready prediction function for equipment failure
    
    Args:
        equipment_data: DataFrame with equipment features
        
    Returns:
        DataFrame with predictions and maintenance urgency
    """
    
    # Load deployment package
    with open('equipment_failure_model_deployment.pkl', 'rb') as f:
        package = pickle.load(f)
    
    model = package['best_model']
    features = package['features']
    
    # Ensure all features are present
    for feature in features:
        if feature not in equipment_data.columns:
            equipment_data[feature] = 0
    
    # Make predictions
    X = equipment_data[features].fillna(0)
    
    # Scale if needed (for neural networks)
    if 'scaler' in package:
        X = package['scaler'].transform(X)
    
    predictions = model.predict(X)
    
    # Create results DataFrame
    results = pd.DataFrame({
        'equipment_id': equipment_data.index if 'equipment_id' not in equipment_data.columns else equipment_data['equipment_id'],
        'failure_probability': predictions,
        'maintenance_urgency': [
            'critical' if p >= 0.7 else 'high' if p >= 0.4 else 'medium' if p >= 0.2 else 'low'
            for p in predictions
        ],
        'recommendation': [
            'Immediate maintenance required' if p >= 0.7 else
            'Schedule maintenance soon' if p >= 0.4 else
            'Monitor closely' if p >= 0.2 else
            'Normal operation'
            for p in predictions
        ]
    })
    
    return results

# Example usage:
# import pandas as pd
# new_equipment = pd.read_csv('new_equipment_data.csv')
# predictions = production_predict(new_equipment)
# predictions.to_csv('maintenance_schedule.csv', index=False)

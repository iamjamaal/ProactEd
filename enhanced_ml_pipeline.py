"""
Enhanced ML Pipeline with Multiple Models and Advanced Features
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import xgboost as xgb
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class AdvancedModelPipeline:
    def __init__(self):
        """Initialize the advanced model pipeline"""
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=200, random_state=42, max_depth=10),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=200, random_state=42, max_depth=6),
            'xgboost': xgb.XGBRegressor(n_estimators=200, random_state=42, max_depth=6),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42, max_iter=1000),
            'linear_regression': LinearRegression()
        }
        self.scalers = {}
        self.model_performance = {}
        self.ensemble_weights = {}
        self.feature_importance = {}
        
    def create_advanced_features(self, df):
        """Create advanced engineered features"""
        df_enhanced = df.copy()
        
        # Time-based features
        if 'age_months' in df.columns:
            df_enhanced['age_years'] = df_enhanced['age_months'] / 12
            df_enhanced['age_category_numeric'] = pd.cut(df_enhanced['age_months'], 
                                                       bins=[0, 12, 36, 60, 120, float('inf')], 
                                                       labels=[1, 2, 3, 4, 5]).astype(float)
        
        # Usage intensity features
        if 'daily_usage_hours' in df.columns and 'age_months' in df.columns:
            df_enhanced['cumulative_usage'] = df_enhanced['daily_usage_hours'] * df_enhanced['age_months'] * 30
            df_enhanced['usage_intensity'] = df_enhanced['daily_usage_hours'] / 12  # Normalized to 12 hours max
        
        # Maintenance efficiency
        if 'maintenance_count' in df.columns and 'age_months' in df.columns:
            df_enhanced['maintenance_frequency'] = df_enhanced['maintenance_count'] / (df_enhanced['age_months'] + 1)
            df_enhanced['time_since_maintenance_ratio'] = df_enhanced['last_maintenance_days'] / (df_enhanced['age_months'] * 30 + 1)
        
        # Environmental stress
        if 'operating_temperature' in df.columns and 'room_temperature' in df.columns:
            df_enhanced['temperature_stress'] = (df_enhanced['operating_temperature'] - df_enhanced['room_temperature']) / df_enhanced['room_temperature']
        
        # Equipment-specific features
        if 'equipment_type' in df.columns:
            # Create equipment-specific thresholds
            equipment_thresholds = {
                'projector': {'temp_max': 55, 'vibration_max': 3.0},
                'air_conditioner': {'temp_max': 45, 'vibration_max': 2.0},
                'podium': {'temp_max': 40, 'vibration_max': 1.5}
            }
            
            df_enhanced['temp_stress_ratio'] = 0
            df_enhanced['vibration_stress_ratio'] = 0
            
            for eq_type, thresholds in equipment_thresholds.items():
                mask = df_enhanced['equipment_type'].str.lower().str.contains(eq_type.lower(), na=False)
                if 'operating_temperature' in df.columns:
                    df_enhanced.loc[mask, 'temp_stress_ratio'] = df_enhanced.loc[mask, 'operating_temperature'] / thresholds['temp_max']
                if 'vibration_level' in df.columns:
                    df_enhanced.loc[mask, 'vibration_stress_ratio'] = df_enhanced.loc[mask, 'vibration_level'] / thresholds['vibration_max']
        
        # Interaction features
        if 'age_months' in df.columns and 'daily_usage_hours' in df.columns:
            df_enhanced['age_usage_interaction'] = df_enhanced['age_months'] * df_enhanced['daily_usage_hours']
        
        # Risk compound features
        stress_columns = [col for col in df_enhanced.columns if 'stress' in col.lower() or 'ratio' in col.lower()]
        if stress_columns:
            df_enhanced['compound_stress'] = df_enhanced[stress_columns].mean(axis=1)
        
        return df_enhanced
    
    def prepare_features(self, df, target_column='failure_probability_clean'):
        """Prepare features for training"""
        df_enhanced = self.create_advanced_features(df)
        
        # Select numeric features only
        numeric_columns = df_enhanced.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove target and ID columns
        feature_columns = [col for col in numeric_columns 
                          if col not in [target_column, 'equipment_id', 'failure_probability']]
        
        X = df_enhanced[feature_columns].fillna(0)
        y = df_enhanced[target_column] if target_column in df_enhanced.columns else None
        
        return X, y, feature_columns
    
    def train_individual_models(self, X, y):
        """Train individual models"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for name, model in self.models.items():
            print(f"Training {name}...")
            
            # Scale features for neural network
            if name == 'neural_network':
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                self.scalers[name] = scaler
                
                model.fit(X_train_scaled, y_train)
                predictions = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
            
            # Calculate performance metrics
            mse = mean_squared_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            
            # Cross-validation score
            if name == 'neural_network':
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            else:
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
            
            self.model_performance[name] = {
                'mse': mse,
                'r2': r2,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            # Feature importance (where available)
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))
            
            print(f"{name}: R² = {r2:.3f}, CV = {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    def create_ensemble_model(self, X, y):
        """Create ensemble model with optimal weights"""
        # Calculate weights based on cross-validation performance
        total_cv_score = sum([perf['cv_mean'] for perf in self.model_performance.values()])
        
        for name, perf in self.model_performance.items():
            self.ensemble_weights[name] = perf['cv_mean'] / total_cv_score
        
        print("\\nEnsemble weights:")
        for name, weight in self.ensemble_weights.items():
            print(f"{name}: {weight:.3f}")
    
    def predict_ensemble(self, X):
        """Make ensemble predictions"""
        predictions = {}
        
        for name, model in self.models.items():
            if name == 'neural_network' and name in self.scalers:
                X_scaled = self.scalers[name].transform(X)
                predictions[name] = model.predict(X_scaled)
            else:
                predictions[name] = model.predict(X)
        
        # Weighted ensemble prediction
        ensemble_pred = np.zeros(len(X))
        for name, pred in predictions.items():
            weight = self.ensemble_weights.get(name, 1.0 / len(predictions))
            ensemble_pred += weight * pred
        
        return ensemble_pred, predictions
    
    def save_enhanced_model_system(self, feature_columns, filename='enhanced_model_system.pkl'):
        """Save the complete enhanced model system"""
        model_system = {
            'models': self.models,
            'scalers': self.scalers,
            'ensemble_weights': self.ensemble_weights,
            'feature_columns': feature_columns,
            'model_performance': self.model_performance,
            'feature_importance': self.feature_importance,
            'creation_date': datetime.now().isoformat(),
            'model_version': '2.0_enhanced'
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_system, f)
        
        print(f"Enhanced model system saved to {filename}")
        return model_system
    
    def generate_model_report(self):
        """Generate comprehensive model performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'model_performance': self.model_performance,
            'ensemble_weights': self.ensemble_weights,
            'best_individual_model': max(self.model_performance.keys(), 
                                       key=lambda x: self.model_performance[x]['r2']),
            'feature_importance_summary': {}
        }
        
        # Aggregate feature importance across models
        all_features = set()
        for model_features in self.feature_importance.values():
            all_features.update(model_features.keys())
        
        for feature in all_features:
            importances = [self.feature_importance[model].get(feature, 0) 
                          for model in self.feature_importance.keys()]
            report['feature_importance_summary'][feature] = {
                'mean_importance': np.mean(importances),
                'std_importance': np.std(importances)
            }
        
        # Save report
        import json
        with open(f'model_performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def train_enhanced_models():
    """Main function to train enhanced models"""
    print("🚀 Starting Enhanced Model Training Pipeline...")
    
    # Load data
    print("📊 Loading data...")
    df = pd.read_csv('cleaned_equipment_data.csv')
    print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Initialize pipeline
    pipeline = AdvancedModelPipeline()
    
    # Prepare features
    print("🔧 Preparing features...")
    X, y, feature_columns = pipeline.prepare_features(df)
    print(f"Features prepared: {len(feature_columns)} features")
    print(f"Top features: {feature_columns[:10]}")
    
    # Train individual models
    print("\\n🧠 Training individual models...")
    pipeline.train_individual_models(X, y)
    
    # Create ensemble
    print("\\n🔗 Creating ensemble model...")
    pipeline.create_ensemble_model(X, y)
    
    # Test ensemble performance
    print("\\n📊 Testing ensemble performance...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    ensemble_pred, individual_preds = pipeline.predict_ensemble(X_test)
    ensemble_r2 = r2_score(y_test, ensemble_pred)
    print(f"Ensemble R² = {ensemble_r2:.3f}")
    
    # Save enhanced model system
    print("\\n💾 Saving enhanced model system...")
    model_system = pipeline.save_enhanced_model_system(feature_columns)
    
    # Generate report
    print("\\n📋 Generating performance report...")
    report = pipeline.generate_model_report()
    
    print("\\n✅ Enhanced model training completed!")
    print(f"Best individual model: {report['best_individual_model']}")
    print(f"Best R²: {pipeline.model_performance[report['best_individual_model']]['r2']:.3f}")
    print(f"Ensemble R²: {ensemble_r2:.3f}")
    
    return pipeline, model_system

if __name__ == "__main__":
    train_enhanced_models()

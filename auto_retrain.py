"""
Automated Model Retraining Pipeline
"""
import pandas as pd
import numpy as np
import pickle
import json
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from database_integration import EquipmentDatabase
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_retraining.log'),
        logging.StreamHandler()
    ]
)

class AutoModelRetrainer:
    def __init__(self, db_path='equipment_monitoring.db'):
        """Initialize automated retraining system"""
        self.db = EquipmentDatabase(db_path)
        self.performance_threshold = 0.80  # Minimum R² score to maintain
        self.min_new_data_points = 100     # Minimum new data points to trigger retraining
        self.retraining_schedule_days = 7   # Retrain every 7 days
        
    def check_retraining_criteria(self):
        """Check if model retraining is needed"""
        criteria = {
            'needs_retraining': False,
            'reasons': [],
            'new_data_points': 0,
            'days_since_last_training': 0,
            'current_performance': None
        }
        
        try:
            # Check for new data since last training
            last_training_date = self._get_last_training_date()
            
            if last_training_date:
                days_since = (datetime.now() - last_training_date).days
                criteria['days_since_last_training'] = days_since
                
                # Check for scheduled retraining
                if days_since >= self.retraining_schedule_days:
                    criteria['needs_retraining'] = True
                    criteria['reasons'].append(f"Scheduled retraining ({days_since} days since last training)")
            else:
                criteria['needs_retraining'] = True
                criteria['reasons'].append("No previous training record found")
            
            # Check for sufficient new data
            new_data_count = self._count_new_data_points(last_training_date)
            criteria['new_data_points'] = new_data_count
            
            if new_data_count >= self.min_new_data_points:
                criteria['needs_retraining'] = True
                criteria['reasons'].append(f"Sufficient new data points ({new_data_count})")
            
            # Check current model performance
            current_performance = self._evaluate_current_model()
            criteria['current_performance'] = current_performance
            
            if current_performance and current_performance < self.performance_threshold:
                criteria['needs_retraining'] = True
                criteria['reasons'].append(f"Performance degraded (R² = {current_performance:.3f})")
            
            return criteria
            
        except Exception as e:
            logging.error(f"Error checking retraining criteria: {e}")
            criteria['needs_retraining'] = True
            criteria['reasons'].append(f"Error in criteria check: {e}")
            return criteria
    
    def _get_last_training_date(self):
        """Get the date of last model training"""
        try:
            # Check for training log file
            if os.path.exists('model_training_log.json'):
                with open('model_training_log.json', 'r') as f:
                    log = json.load(f)
                    return datetime.fromisoformat(log['last_training_date'])
            return None
        except:
            return None
    
    def _count_new_data_points(self, since_date):
        """Count new data points since last training"""
        if not since_date:
            # If no previous training, count all data
            equipment_data = self.db.get_equipment_data()
            return len(equipment_data)
        
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                query = '''
                    SELECT COUNT(*) as count 
                    FROM equipment_readings 
                    WHERE timestamp > ?
                '''
                result = pd.read_sql_query(query, conn, params=[since_date])
                return result.iloc[0]['count']
        except:
            return 0
    
    def _evaluate_current_model(self):
        """Evaluate current model performance on recent data"""
        try:
            # Load current model
            if not os.path.exists('complete_equipment_failure_prediction_system.pkl'):
                return None
            
            with open('complete_equipment_failure_prediction_system.pkl', 'rb') as f:
                model_system = pickle.load(f)
            
            model = model_system['model_info']['model_object']
            features = model_system['model_info']['features']
            
            # Get recent data for evaluation
            ml_data = self.db.export_data_for_ml('temp_eval_data.csv')
            
            if ml_data.empty or 'failure_probability' not in ml_data.columns:
                return None
            
            # Prepare features
            for feature in features:
                if feature not in ml_data.columns:
                    ml_data[feature] = 0
            
            X = ml_data[features].fillna(0)
            y = ml_data['failure_probability']
            
            # Make predictions and calculate R²
            predictions = model.predict(X)
            r2 = r2_score(y, predictions)
            
            # Clean up temp file
            if os.path.exists('temp_eval_data.csv'):
                os.remove('temp_eval_data.csv')
            
            return r2
            
        except Exception as e:
            logging.error(f"Error evaluating current model: {e}")
            return None
    
    def _ensure_database_has_data(self):
        """Ensure database has data, import from CSV if needed"""
        try:
            # Check if database has data
            equipment_count = len(self.db.get_equipment_data())
            
            if equipment_count == 0:
                logging.info("Database is empty, importing data from CSV...")
                
                # Try to import from main dataset
                if os.path.exists('knust_classroom_equipment_dataset.csv'):
                    self.db.import_csv_data('knust_classroom_equipment_dataset.csv')
                    logging.info("Data imported from knust_classroom_equipment_dataset.csv")
                elif os.path.exists('cleaned_equipment_data.csv'):
                    self.db.import_csv_data('cleaned_equipment_data.csv')
                    logging.info("Data imported from cleaned_equipment_data.csv")
                else:
                    logging.warning("No CSV data file found to import")
        except Exception as e:
            logging.error(f"Error ensuring database has data: {e}")
    
    def _load_training_data_from_csv(self):
        """Load training data directly from CSV files as fallback"""
        try:
            # Try different CSV files in order of preference
            csv_files = [
                'knust_classroom_equipment_dataset.csv',
                'cleaned_equipment_data.csv',
                'clean_equipment_data.csv'
            ]
            
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    logging.info(f"Loading training data from {csv_file}")
                    df = pd.read_csv(csv_file)
                    
                    # Ensure required columns exist
                    if 'failure_probability' in df.columns or 'failure_probability_clean' in df.columns:
                        # Use failure_probability_clean if available, otherwise failure_probability
                        if 'failure_probability_clean' in df.columns and 'failure_probability' not in df.columns:
                            df['failure_probability'] = df['failure_probability_clean']
                        
                        logging.info(f"Loaded {len(df)} samples from {csv_file}")
                        return df
                    else:
                        logging.warning(f"{csv_file} doesn't contain failure_probability column")
            
            logging.error("No suitable CSV file found with failure_probability data")
            return pd.DataFrame()
            
        except Exception as e:
            logging.error(f"Error loading training data from CSV: {e}")
            return pd.DataFrame()
    
    def retrain_model(self):
        """Retrain the model with latest data"""
        try:
            logging.info("Starting model retraining...")
            
            # First, ensure database has data
            self._ensure_database_has_data()
            
            # Export latest data
            training_data = self.db.export_data_for_ml('retraining_data.csv')
            
            if training_data.empty:
                # If database export fails, try to use CSV files directly
                logging.warning("Database export empty, trying CSV files...")
                training_data = self._load_training_data_from_csv()
            
            if training_data.empty:
                logging.error("No training data available from any source")
                return False
            
            logging.info(f"Training data: {len(training_data)} samples")
            
            # Prepare features and target
            target_col = 'failure_probability'
            if target_col not in training_data.columns:
                logging.error(f"Target column '{target_col}' not found")
                return False
            
            # Select numeric features
            numeric_cols = training_data.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [col for col in numeric_cols if col != target_col]
            
            X = training_data[feature_cols].fillna(0)
            y = training_data[target_col]
            
            logging.info(f"Features: {len(feature_cols)}")
            logging.info(f"Feature names: {feature_cols[:10]}...")  # Log first 10 features
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train new model
            model = RandomForestRegressor(n_estimators=200, random_state=42, max_depth=10, n_jobs=-1)
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_predictions = model.predict(X_train)
            test_predictions = model.predict(X_test)
            
            train_r2 = r2_score(y_train, train_predictions)
            test_r2 = r2_score(y_test, test_predictions)
            test_mse = mean_squared_error(y_test, test_predictions)
            
            logging.info(f"Model performance - Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")
            
            # Create new model system
            model_system = {
                'model_info': {
                    'model_name': 'Random Forest (Retrained)',
                    'model_object': model,
                    'features': feature_cols,
                    'optimal_threshold': 0.5,  # Default threshold
                    'performance_metrics': {
                        'r2_score': test_r2,
                        'mse': test_mse,
                        'train_r2': train_r2,
                        'roi': 250.0  # Estimated ROI
                    }
                },
                'training_info': {
                    'training_date': datetime.now().isoformat(),
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'feature_count': len(feature_cols),
                    'retraining_version': 'auto_v1.0'
                }
            }
            
            # Save retrained model
            retrained_filename = f'retrained_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
            with open(retrained_filename, 'wb') as f:
                pickle.dump(model_system, f)
            
            logging.info(f"Retrained model saved: {retrained_filename}")
            
            # Update main model if performance is better
            current_performance = self._evaluate_current_model()
            if current_performance is None or test_r2 > current_performance:
                # Backup current model
                if os.path.exists('complete_equipment_failure_prediction_system.pkl'):
                    backup_name = f'model_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
                    os.rename('complete_equipment_failure_prediction_system.pkl', backup_name)
                    logging.info(f"Backed up current model: {backup_name}")
                
                # Replace with retrained model
                os.rename(retrained_filename, 'complete_equipment_failure_prediction_system.pkl')
                logging.info("Retrained model promoted to production")
            else:
                logging.info("Retrained model performance not better than current, keeping current model")
            
            # Update training log
            self._update_training_log(test_r2, len(training_data))
            
            # Generate retraining report
            self._generate_retraining_report(model_system, len(training_data), test_r2)
            
            # Clean up
            if os.path.exists('retraining_data.csv'):
                os.remove('retraining_data.csv')
            
            return True
            
        except Exception as e:
            logging.error(f"Error during model retraining: {e}")
            return False
    
    def _update_training_log(self, performance, sample_count):
        """Update training log"""
        log_entry = {
            'last_training_date': datetime.now().isoformat(),
            'performance': performance,
            'sample_count': sample_count,
            'training_type': 'automated_retraining'
        }
        
        with open('model_training_log.json', 'w') as f:
            json.dump(log_entry, f, indent=2)
    
    def _generate_retraining_report(self, model_system, sample_count, performance):
        """Generate retraining report"""
        report = {
            'retraining_timestamp': datetime.now().isoformat(),
            'model_performance': {
                'r2_score': performance,
                'sample_count': sample_count,
                'feature_count': len(model_system['model_info']['features'])
            },
            'training_info': model_system['training_info'],
            'status': 'completed_successfully'
        }
        
        report_filename = f'retraining_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"Retraining report saved: {report_filename}")
    
    def run_automated_check(self):
        """Run automated retraining check"""
        logging.info("Running automated retraining check...")
        
        criteria = self.check_retraining_criteria()
        
        logging.info(f"Retraining needed: {criteria['needs_retraining']}")
        if criteria['reasons']:
            logging.info(f"Reasons: {', '.join(criteria['reasons'])}")
        
        if criteria['needs_retraining']:
            logging.info("Starting automated retraining...")
            success = self.retrain_model()
            
            if success:
                logging.info("[SUCCESS] Automated retraining completed successfully")
            else:
                logging.error("[FAILED] Automated retraining failed")
            
            return success
        else:
            logging.info("[SUCCESS] No retraining needed at this time")
            return True

def main():
    """Main function for automated retraining"""
    print("Robot Automated Model Retraining System")
    print("=" * 50)
    
    retrainer = AutoModelRetrainer()
    
    # Run automated check and retraining if needed
    success = retrainer.run_automated_check()
    
    if success:
        print("\\n[SUCCESS] Automated retraining process completed successfully!")
    else:
        print("\\n[FAILED] Automated retraining process failed. Check logs for details.")

if __name__ == "__main__":
    main()

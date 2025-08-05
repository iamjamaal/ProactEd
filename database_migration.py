"""
Advanced Database Migration and Validation Tools
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from database_integration import EquipmentDatabase

class DatabaseMigrationTool:
    def __init__(self, db_path='equipment_monitoring.db'):
        """Initialize migration tool"""
        self.db_path = db_path
        self.validation_results = {}
        
    def validate_csv_data(self, csv_file='cleaned_equipment_data.csv'):
        """Comprehensive validation of CSV data before import"""
        try:
            df = pd.read_csv(csv_file)
            validation = {
                'file_info': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'file_size_mb': round(df.memory_usage(deep=True).sum() / 1024**2, 2)
                },
                'data_quality': {},
                'missing_columns': [],
                'data_types': {},
                'issues': [],
                'recommendations': []
            }
            
            # Required columns for equipment
            required_equipment_cols = ['equipment_type', 'age_months']
            optional_equipment_cols = ['equipment_id', 'room_id', 'room_type', 'installation_date']
            
            # Required columns for sensor readings  
            sensor_cols = ['operating_temperature', 'vibration_level', 'power_consumption', 
                          'humidity_level', 'dust_accumulation', 'performance_score', 'daily_usage_hours']
            
            # Required columns for predictions
            prediction_cols = ['failure_probability_clean']
            
            # Check for missing required columns
            for col in required_equipment_cols:
                if col not in df.columns:
                    validation['missing_columns'].append(col)
                    validation['issues'].append(f"Missing required column: {col}")
            
            # Generate equipment_id if missing
            if 'equipment_id' not in df.columns:
                validation['recommendations'].append("Will generate equipment_id column automatically")
            
            # Data quality checks
            for col in df.columns:
                col_data = df[col]
                validation['data_quality'][col] = {
                    'missing_count': col_data.isnull().sum(),
                    'missing_percentage': round(col_data.isnull().sum() / len(df) * 100, 2),
                    'unique_values': col_data.nunique(),
                    'data_type': str(col_data.dtype)
                }
                
                # Check for high missing data
                if col_data.isnull().sum() / len(df) > 0.5:
                    validation['issues'].append(f"Column '{col}' has >50% missing data")
                
                # Check data ranges for sensor columns
                if col in ['operating_temperature', 'vibration_level', 'power_consumption']:
                    if col_data.min() < 0:
                        validation['issues'].append(f"Column '{col}' has negative values")
                    if col == 'operating_temperature' and col_data.max() > 100:
                        validation['issues'].append(f"Column '{col}' has unrealistic high values (>100°C)")
                
                # Check failure probability
                if 'failure_probability' in col:
                    if col_data.min() < 0 or col_data.max() > 1:
                        validation['issues'].append(f"Column '{col}' should be between 0 and 1")
            
            # Equipment type validation
            if 'equipment_type' in df.columns:
                equipment_types = df['equipment_type'].value_counts()
                validation['equipment_distribution'] = equipment_types.to_dict()
                
                # Check for consistent naming
                unique_types = df['equipment_type'].str.lower().unique()
                if len(unique_types) != len(df['equipment_type'].unique()):
                    validation['issues'].append("Equipment types have inconsistent capitalization")
                    validation['recommendations'].append("Will standardize equipment type names")
            
            # Age validation
            if 'age_months' in df.columns:
                age_stats = df['age_months'].describe()
                if age_stats['max'] > 360:  # 30 years
                    validation['issues'].append("Some equipment appears very old (>30 years)")
                if age_stats['min'] < 0:
                    validation['issues'].append("Some equipment has negative age")
            
            self.validation_results = validation
            
            # Save validation report
            with open(f'data_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                json.dump(validation, f, indent=2)
            
            return validation
            
        except Exception as e:
            logging.error(f"Error validating CSV data: {e}")
            return None
    
    def migrate_with_validation(self, csv_file='cleaned_equipment_data.csv'):
        """Migrate data with comprehensive validation and cleanup"""
        
        # Step 1: Validate data
        print("🔍 Step 1: Validating data...")
        validation = self.validate_csv_data(csv_file)
        
        if not validation:
            print("❌ Data validation failed")
            return False
        
        print(f"✅ Data validation completed:")
        print(f"   - Total rows: {validation['file_info']['total_rows']}")
        print(f"   - Total columns: {validation['file_info']['total_columns']}")
        print(f"   - Issues found: {len(validation['issues'])}")
        
        if validation['issues']:
            print("⚠️ Issues found:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        
        # Step 2: Clean and prepare data
        print("\\n🧹 Step 2: Cleaning data...")
        df = pd.read_csv(csv_file)
        
        # Generate equipment_id if missing
        if 'equipment_id' not in df.columns:
            df['equipment_id'] = [f"EQ-{i:03d}" for i in range(len(df))]
            print("   ✅ Generated equipment_id column")
        
        # Standardize equipment types
        if 'equipment_type' in df.columns:
            equipment_mapping = {
                'proj': 'projector',
                'projector': 'projector', 
                'ac': 'air_conditioner',
                'air conditioner': 'air_conditioner',
                'air_conditioner': 'air_conditioner',
                'aircon': 'air_conditioner',
                'pod': 'podium',
                'podium': 'podium'
            }
            df['equipment_type'] = df['equipment_type'].str.lower().map(equipment_mapping).fillna(df['equipment_type'])
            print("   ✅ Standardized equipment types")
        
        # Clean numeric data
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            # Replace negative values with 0 for certain columns
            if col in ['operating_temperature', 'vibration_level', 'power_consumption', 'age_months']:
                if (df[col] < 0).any():
                    df.loc[df[col] < 0, col] = 0
                    print(f"   ✅ Cleaned negative values in {col}")
        
        # Step 3: Initialize database
        print("\\n💾 Step 3: Initializing database...")
        db = EquipmentDatabase(self.db_path)
        
        # Step 4: Import technicians data
        print("\\n👷 Step 4: Importing technician data...")
        self._import_technician_data(db)
        
        # Step 5: Import equipment data
        print("\\n🏭 Step 5: Importing equipment data...")
        success = self._import_equipment_data(db, df)
        
        if success:
            print("\\n✅ Migration completed successfully!")
            
            # Generate migration report
            self._generate_migration_report(db, validation)
            return True
        else:
            print("\\n❌ Migration failed")
            return False
    
    def _import_technician_data(self, db):
        """Import default technician data"""
        technicians = [
            {
                'technician_id': 'TECH-001',
                'name': 'Noah Jamal Nabila',
                'email': 'noahjamal303@gmail.com',
                'specializations': 'General Maintenance,Electrical Systems,Mechanical Systems',
                'hourly_rate': 90,
                'max_capacity': 40
            },
            {
                'technician_id': 'TECH-002', 
                'name': 'Ama Serwaa',
                'email': 'amaserwaa@gmail.com',
                'specializations': 'Podium Maintenance,Audio Equipment,Conference Systems',
                'hourly_rate': 77,
                'max_capacity': 40
            },
            {
                'technician_id': 'TECH-003',
                'name': 'Momoreoluwa Monsuru-Oke',
                'email': 'momoreoke@gmail.com', 
                'specializations': 'General Maintenance,Preventive Maintenance,Equipment Diagnostics',
                'hourly_rate': 88,
                'max_capacity': 40
            }
        ]
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            for tech in technicians:
                cursor.execute('''
                    INSERT OR REPLACE INTO technicians 
                    (technician_id, name, email, specializations, hourly_rate, max_capacity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    tech['technician_id'], tech['name'], tech['email'],
                    tech['specializations'], tech['hourly_rate'], tech['max_capacity']
                ))
            
            conn.commit()
            print(f"   ✅ Imported {len(technicians)} technicians")
    
    def _import_equipment_data(self, db, df):
        """Import equipment data with error handling"""
        try:
            with sqlite3.connect(db.db_path) as conn:
                # Import equipment info
                equipment_columns = ['equipment_id', 'equipment_type', 'room_id', 'room_type', 
                                   'installation_date', 'age_months']
                available_columns = [col for col in equipment_columns if col in df.columns]
                equipment_df = df[available_columns].drop_duplicates('equipment_id')
                
                # Add default values
                equipment_df['manufacturer'] = 'Unknown'
                equipment_df['model'] = 'Unknown'
                equipment_df['status'] = 'operational'
                
                equipment_df.to_sql('equipment', conn, if_exists='replace', index=False)
                print(f"   ✅ Imported {len(equipment_df)} equipment records")
                
                # Import sensor readings
                sensor_columns = ['equipment_id', 'operating_temperature', 'vibration_level',
                                'power_consumption', 'humidity_level', 'dust_accumulation',
                                'performance_score', 'daily_usage_hours']
                available_sensor_cols = [col for col in sensor_columns if col in df.columns]
                
                if len(available_sensor_cols) > 1:  # At least equipment_id + one sensor
                    readings_df = df[available_sensor_cols].copy()
                    readings_df['timestamp'] = datetime.now()
                    readings_df.to_sql('equipment_readings', conn, if_exists='replace', index=False)
                    print(f"   ✅ Imported {len(readings_df)} sensor readings")
                
                # Import predictions
                if 'failure_probability_clean' in df.columns:
                    predictions_df = df[['equipment_id', 'failure_probability_clean']].copy()
                    predictions_df.rename(columns={'failure_probability_clean': 'failure_probability'}, inplace=True)
                    predictions_df['prediction_date'] = datetime.now()
                    predictions_df['model_version'] = '1.0'
                    predictions_df['risk_level'] = predictions_df['failure_probability'].apply(
                        lambda x: 'Critical' if x >= 0.7 else 'High' if x >= 0.5 else 'Medium' if x >= 0.3 else 'Low'
                    )
                    
                    # Calculate health scores
                    predictions_df['health_score'] = 100 - (predictions_df['failure_probability'] * 100)
                    
                    predictions_df.to_sql('failure_predictions', conn, if_exists='replace', index=False)
                    print(f"   ✅ Imported {len(predictions_df)} failure predictions")
                
                return True
                
        except Exception as e:
            logging.error(f"Error importing equipment data: {e}")
            return False
    
    def _generate_migration_report(self, db, validation):
        """Generate comprehensive migration report"""
        metrics = db.get_dashboard_metrics()
        
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'validation_summary': {
                'total_issues': len(validation['issues']),
                'issues': validation['issues'],
                'recommendations_applied': validation['recommendations']
            },
            'migration_results': {
                'total_equipment': metrics['total_equipment'],
                'risk_distribution': metrics['risk_distribution'],
                'database_file': db.db_path,
                'tables_created': ['equipment', 'equipment_readings', 'failure_predictions', 
                                 'maintenance_records', 'alerts', 'technicians']
            },
            'next_steps': [
                'Run dashboard: streamlit run dashboard.py',
                'Test API: python equipment_api.py',
                'Start monitoring: python equipment_monitor.py',
                'Access database: python database_integration.py'
            ]
        }
        
        report_file = f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\\n📋 Migration report saved: {report_file}")
        print(f"\\n📊 Final Statistics:")
        print(f"   - Total equipment: {metrics['total_equipment']}")
        print(f"   - Database file: {db.db_path}")
        
        if metrics['risk_distribution']:
            print("   - Risk distribution:")
            for risk in metrics['risk_distribution']:
                print(f"     {risk['risk_level']}: {risk['count']}")

def main():
    """Main migration function"""
    print("🚀 Starting Advanced Database Migration...")
    
    migration_tool = DatabaseMigrationTool()
    success = migration_tool.migrate_with_validation()
    
    if success:
        print("\\n🎉 Migration completed successfully!")
        print("\\n🔧 Next steps:")
        print("   1. Test dashboard: streamlit run dashboard.py")
        print("   2. Start monitoring: python equipment_monitor.py") 
        print("   3. Train enhanced models: python enhanced_ml_pipeline.py")
    else:
        print("\\n❌ Migration failed. Check logs for details.")

if __name__ == "__main__":
    main()

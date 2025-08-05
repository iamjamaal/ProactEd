"""
Database Integration for Equipment Failure Prediction System
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EquipmentDatabase:
    def __init__(self, db_path='equipment_monitoring.db'):
        """Initialize the equipment database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Equipment table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    equipment_id TEXT PRIMARY KEY,
                    equipment_type TEXT NOT NULL,
                    room_id TEXT,
                    room_type TEXT,
                    installation_date DATE,
                    age_months INTEGER,
                    manufacturer TEXT,
                    model TEXT,
                    status TEXT DEFAULT 'operational',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Equipment readings table (sensor data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operating_temperature REAL,
                    vibration_level REAL,
                    power_consumption REAL,
                    humidity_level REAL,
                    dust_accumulation REAL,
                    performance_score REAL,
                    daily_usage_hours REAL,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
                )
            ''')
            
            # Failure predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failure_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failure_probability REAL NOT NULL,
                    health_score REAL,
                    risk_level TEXT,
                    model_version TEXT,
                    confidence_interval REAL,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
                )
            ''')
            
            # Maintenance records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    work_order_id TEXT UNIQUE,
                    maintenance_type TEXT NOT NULL,
                    scheduled_date DATE,
                    completion_date DATE,
                    technician_id TEXT,
                    technician_name TEXT,
                    status TEXT DEFAULT 'scheduled',
                    estimated_cost REAL,
                    actual_cost REAL,
                    completion_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    alert_type TEXT,
                    failure_probability REAL,
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
                )
            ''')
            
            # Technicians table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS technicians (
                    technician_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    specializations TEXT,
                    hourly_rate REAL,
                    max_capacity INTEGER DEFAULT 40,
                    current_workload INTEGER DEFAULT 0,
                    availability TEXT DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def import_csv_data(self, csv_file='cleaned_equipment_data.csv'):
        """Import existing CSV data into database"""
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"Importing {len(df)} records from {csv_file}")
            
            # Check if equipment_id exists, if not create it
            if 'equipment_id' not in df.columns:
                df['equipment_id'] = [f"EQ-{i:03d}" for i in range(len(df))]
                logger.info("Generated equipment_id column")
            
            with sqlite3.connect(self.db_path) as conn:
                # Import equipment basic info
                base_columns = ['equipment_id', 'equipment_type', 'room_id', 'room_type', 
                               'installation_date', 'age_months']
                available_columns = [col for col in base_columns if col in df.columns]
                equipment_df = df[available_columns].drop_duplicates('equipment_id')
                
                # Add default values for missing columns
                equipment_df['manufacturer'] = 'Unknown'
                equipment_df['model'] = 'Unknown'
                equipment_df['status'] = 'operational'
                
                equipment_df.to_sql('equipment', conn, if_exists='replace', index=False)
                
                # Import sensor readings
                readings_columns = ['equipment_id', 'operating_temperature', 'vibration_level',
                                  'power_consumption', 'humidity_level', 'dust_accumulation',
                                  'performance_score', 'daily_usage_hours']
                
                readings_df = df[readings_columns].copy()
                readings_df['timestamp'] = datetime.now()
                
                readings_df.to_sql('equipment_readings', conn, if_exists='replace', index=False)
                
                # Import failure predictions if available
                failure_prob_col = None
                if 'failure_probability_clean' in df.columns:
                    failure_prob_col = 'failure_probability_clean'
                elif 'failure_probability' in df.columns:
                    failure_prob_col = 'failure_probability'
                
                if failure_prob_col:
                    predictions_df = df[['equipment_id', failure_prob_col]].copy()
                    predictions_df.rename(columns={failure_prob_col: 'failure_probability'}, inplace=True)
                    predictions_df['prediction_date'] = datetime.now()
                    predictions_df['model_version'] = '1.0'
                    predictions_df['health_score'] = 1.0 - predictions_df['failure_probability']  # Inverse of failure probability
                    predictions_df['risk_level'] = predictions_df['failure_probability'].apply(
                        lambda x: 'Critical' if x >= 0.7 else 'High' if x >= 0.5 else 'Medium' if x >= 0.3 else 'Low'
                    )
                    
                    predictions_df.to_sql('failure_predictions', conn, if_exists='replace', index=False)
                    logger.info(f"Imported {len(predictions_df)} failure predictions")
                else:
                    logger.warning("No failure probability column found in CSV")
                
                logger.info("CSV data imported successfully")
                
        except Exception as e:
            logger.error(f"Error importing CSV data: {e}")
    
    def add_equipment(self, equipment_data):
        """Add new equipment to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO equipment 
                (equipment_id, equipment_type, room_id, room_type, installation_date, 
                 age_months, manufacturer, model, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipment_data['equipment_id'],
                equipment_data['equipment_type'],
                equipment_data.get('room_id'),
                equipment_data.get('room_type'),
                equipment_data.get('installation_date'),
                equipment_data.get('age_months'),
                equipment_data.get('manufacturer', 'Unknown'),
                equipment_data.get('model', 'Unknown'),
                equipment_data.get('status', 'operational'),
                datetime.now()
            ))
            
            conn.commit()
    
    def add_sensor_reading(self, equipment_id, reading_data):
        """Add new sensor reading"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO equipment_readings 
                (equipment_id, operating_temperature, vibration_level, power_consumption,
                 humidity_level, dust_accumulation, performance_score, daily_usage_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipment_id,
                reading_data.get('operating_temperature'),
                reading_data.get('vibration_level'),
                reading_data.get('power_consumption'),
                reading_data.get('humidity_level'),
                reading_data.get('dust_accumulation'),
                reading_data.get('performance_score'),
                reading_data.get('daily_usage_hours')
            ))
            
            conn.commit()
    
    def add_prediction(self, equipment_id, prediction_data):
        """Add failure prediction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO failure_predictions 
                (equipment_id, failure_probability, health_score, risk_level, 
                 model_version, confidence_interval)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                equipment_id,
                prediction_data['failure_probability'],
                prediction_data.get('health_score'),
                prediction_data.get('risk_level'),
                prediction_data.get('model_version', '1.0'),
                prediction_data.get('confidence_interval')
            ))
            
            conn.commit()
    
    def get_equipment_data(self, equipment_id=None, equipment_type=None):
        """Get equipment data with latest readings and predictions"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT e.*, 
                       r.operating_temperature, r.vibration_level, r.power_consumption,
                       r.humidity_level, r.dust_accumulation, r.performance_score,
                       r.daily_usage_hours, r.timestamp as reading_timestamp,
                       p.failure_probability, p.health_score, p.risk_level,
                       p.prediction_date
                FROM equipment e
                LEFT JOIN (
                    SELECT equipment_id, operating_temperature, vibration_level, 
                           power_consumption, humidity_level, dust_accumulation,
                           performance_score, daily_usage_hours, timestamp,
                           ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY timestamp DESC) as rn
                    FROM equipment_readings
                ) r ON e.equipment_id = r.equipment_id AND r.rn = 1
                LEFT JOIN (
                    SELECT equipment_id, failure_probability, health_score, risk_level,
                           prediction_date,
                           ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY prediction_date DESC) as rn
                    FROM failure_predictions
                ) p ON e.equipment_id = p.equipment_id AND p.rn = 1
            '''
            
            conditions = []
            params = []
            
            if equipment_id:
                conditions.append("e.equipment_id = ?")
                params.append(equipment_id)
            
            if equipment_type:
                conditions.append("e.equipment_type = ?")
                params.append(equipment_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
    
    def get_maintenance_schedule(self, days_ahead=30):
        """Get maintenance schedule for next N days"""
        with sqlite3.connect(self.db_path) as conn:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            query = '''
                SELECT m.*, e.equipment_type, e.room_id
                FROM maintenance_records m
                JOIN equipment e ON m.equipment_id = e.equipment_id
                WHERE m.scheduled_date BETWEEN ? AND ?
                AND m.status IN ('scheduled', 'in_progress')
                ORDER BY m.scheduled_date, m.equipment_id
            '''
            
            df = pd.read_sql_query(query, conn, params=[datetime.now().date(), end_date.date()])
            return df
    
    def get_active_alerts(self):
        """Get active (unacknowledged) alerts"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT a.*, e.equipment_type, e.room_id
                FROM alerts a
                JOIN equipment e ON a.equipment_id = e.equipment_id
                WHERE a.acknowledged = FALSE
                ORDER BY a.created_at DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            return df
    
    def create_alert(self, equipment_id, alert_data):
        """Create new alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (equipment_id, alert_level, alert_type, failure_probability, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                equipment_id,
                alert_data['alert_level'],
                alert_data.get('alert_type', 'failure_risk'),
                alert_data.get('failure_probability'),
                alert_data.get('message')
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def schedule_maintenance(self, equipment_id, maintenance_data, technician_id=None):
        """Schedule maintenance and create associated alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert maintenance record
            cursor.execute('''
                INSERT INTO maintenance_records 
                (equipment_id, scheduled_date, maintenance_type, technician_id, 
                 status, estimated_cost, completion_notes)
                VALUES (?, ?, ?, ?, 'scheduled', ?, ?)
            ''', (
                equipment_id,
                maintenance_data.get('scheduled_date'),
                maintenance_data.get('maintenance_type', 'preventive'),
                technician_id,
                maintenance_data.get('estimated_cost', 0),
                maintenance_data.get('description', 'Scheduled maintenance'),
            ))
            
            maintenance_id = cursor.lastrowid
            
            # Create alert for scheduled maintenance
            alert_data = {
                'alert_level': maintenance_data.get('priority', 'medium'),
                'alert_type': 'maintenance_scheduled',
                'message': f"Maintenance scheduled for {maintenance_data.get('scheduled_date')} - {maintenance_data.get('maintenance_type', 'preventive')}",
                'created_at': datetime.now().isoformat(),
                'acknowledged': False
            }
            
            # Create the alert
            alert_id = self.create_alert(equipment_id, alert_data)
            
            conn.commit()
            
            logging.info(f"Maintenance scheduled for {equipment_id} with alert {alert_id}")
            return maintenance_id
    
    def assign_technician_to_maintenance(self, maintenance_id, technician_id):
        """Assign technician to maintenance and update alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update maintenance record
            cursor.execute('''
                UPDATE maintenance_records 
                SET technician_id = ?
                WHERE id = ?
            ''', (technician_id, maintenance_id))
            
            # Get maintenance details for alert update
            maintenance_info = pd.read_sql_query('''
                SELECT equipment_id, scheduled_date, maintenance_type 
                FROM maintenance_records 
                WHERE id = ?
            ''', conn, params=[maintenance_id])
            
            if not maintenance_info.empty:
                equipment_id = maintenance_info.iloc[0]['equipment_id']
                scheduled_date = maintenance_info.iloc[0]['scheduled_date']
                maintenance_type = maintenance_info.iloc[0]['maintenance_type']
                
                # Create new alert for technician assignment
                alert_data = {
                    'alert_level': 'medium',
                    'alert_type': 'technician_assigned',
                    'message': f"Technician {technician_id} assigned to {maintenance_type} on {scheduled_date}",
                    'created_at': datetime.now().isoformat(),
                    'acknowledged': False
                }
                
                self.create_alert(equipment_id, alert_data)
            
            conn.commit()
            logging.info(f"Technician {technician_id} assigned to maintenance {maintenance_id}")
    
    def acknowledge_alert(self, alert_id, acknowledged_by):
        """Acknowledge an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_by = ?, acknowledged_at = ?
                WHERE id = ?
            ''', (acknowledged_by, datetime.now(), alert_id))
            
            conn.commit()
    
    def get_equipment_history(self, equipment_id, days_back=30):
        """Get equipment history for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Get readings history
            readings_query = '''
                SELECT * FROM equipment_readings 
                WHERE equipment_id = ? AND timestamp >= ?
                ORDER BY timestamp
            '''
            readings_df = pd.read_sql_query(readings_query, conn, params=[equipment_id, start_date])
            
            # Get predictions history
            predictions_query = '''
                SELECT * FROM failure_predictions 
                WHERE equipment_id = ? AND prediction_date >= ?
                ORDER BY prediction_date
            '''
            predictions_df = pd.read_sql_query(predictions_query, conn, params=[equipment_id, start_date])
            
            # Get maintenance history
            maintenance_query = '''
                SELECT * FROM maintenance_records 
                WHERE equipment_id = ? AND (scheduled_date >= ? OR completion_date >= ?)
                ORDER BY scheduled_date
            '''
            maintenance_df = pd.read_sql_query(maintenance_query, conn, params=[equipment_id, start_date, start_date])
            
            return {
                'readings': readings_df,
                'predictions': predictions_df,
                'maintenance': maintenance_df
            }
    
    def get_dashboard_metrics(self):
        """Get key metrics for dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            metrics = {}
            
            # Total equipment count
            metrics['total_equipment'] = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM equipment", conn
            ).iloc[0]['count']
            
            # Equipment by risk level
            risk_query = '''
                SELECT risk_level, COUNT(*) as count
                FROM (
                    SELECT equipment_id, risk_level,
                           ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY prediction_date DESC) as rn
                    FROM failure_predictions
                ) p
                WHERE p.rn = 1
                GROUP BY risk_level
            '''
            metrics['risk_distribution'] = pd.read_sql_query(risk_query, conn).to_dict('records')
            
            # Active alerts count
            metrics['active_alerts'] = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM alerts WHERE acknowledged = FALSE", conn
            ).iloc[0]['count']
            
            # Upcoming maintenance (next 7 days)
            end_date = datetime.now() + timedelta(days=7)
            metrics['upcoming_maintenance'] = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM maintenance_records WHERE scheduled_date BETWEEN ? AND ? AND status = 'scheduled'",
                conn, params=[datetime.now().date(), end_date.date()]
            ).iloc[0]['count']
            
            return metrics
    
    def export_data_for_ml(self, output_file='ml_training_data.csv'):
        """Export data in format suitable for ML training"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT e.equipment_id, e.equipment_type, e.room_type, e.age_months,
                       r.operating_temperature, r.vibration_level, r.power_consumption,
                       r.humidity_level, r.dust_accumulation, r.performance_score,
                       r.daily_usage_hours,
                       p.failure_probability, p.risk_level
                FROM equipment e
                JOIN equipment_readings r ON e.equipment_id = r.equipment_id
                JOIN failure_predictions p ON e.equipment_id = p.equipment_id
                WHERE r.timestamp = (
                    SELECT MAX(timestamp) FROM equipment_readings r2 
                    WHERE r2.equipment_id = e.equipment_id
                )
                AND p.prediction_date = (
                    SELECT MAX(prediction_date) FROM failure_predictions p2
                    WHERE p2.equipment_id = e.equipment_id
                )
            '''
            
            df = pd.read_sql_query(query, conn)
            df.to_csv(output_file, index=False)
            logger.info(f"ML training data exported to {output_file}")
            return df

def main():
    """Main function for database setup and testing"""
    # Initialize database
    db = EquipmentDatabase()
    
    # Import existing CSV data
    db.import_csv_data()
    
    # Get dashboard metrics
    metrics = db.get_dashboard_metrics()
    print("Dashboard Metrics:")
    print(json.dumps(metrics, indent=2))
    
    # Export data for ML
    ml_data = db.export_data_for_ml()
    print(f"\\nExported {len(ml_data)} records for ML training")

if __name__ == "__main__":
    main()

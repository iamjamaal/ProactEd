"""
Real-Time Equipment Monitoring System
"""
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import logging
from database_integration import EquipmentDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('equipment_monitoring.log'),
        logging.StreamHandler()
    ]
)

class EquipmentMonitor:
    def __init__(self, model_path='complete_equipment_failure_prediction_system.pkl'):
        """Initialize the monitoring system"""
        self.model_path = model_path
        self.db = EquipmentDatabase()  # Add database integration
        self.alert_thresholds = {
            'critical': 0.7,
            'high': 0.5,
            'medium': 0.3
        }
        self.monitoring_active = False
        # Remove self.alert_history - now using database
        
    def load_current_equipment_data(self):
        """Load current equipment data for monitoring"""
        try:
            # Try to load from database first
            equipment_data = self.db.get_equipment_data()
            
            if not equipment_data.empty:
                logging.info(f"Loaded {len(equipment_data)} equipment records from database")
                return equipment_data
            else:
                # Fallback to CSV if database is empty
                logging.warning("Database empty, loading from CSV")
                df = pd.read_csv('cleaned_equipment_data.csv')
                
                # Simulate real-time data updates
                # Add some random variation to simulate sensor readings
                for idx in df.index:
                    if np.random.random() < 0.1:  # 10% chance of change
                        # Simulate equipment degradation over time
                        if 'operating_temperature' in df.columns:
                            df.loc[idx, 'operating_temperature'] += np.random.normal(0, 2)
                        if 'vibration_level' in df.columns:
                            df.loc[idx, 'vibration_level'] += np.random.normal(0, 0.5)
                        if 'power_consumption' in df.columns:
                            df.loc[idx, 'power_consumption'] += np.random.normal(0, 10)
                
                return df
        except Exception as e:
            logging.error(f"Error loading equipment data: {e}")
            return None
    
    def predict_failures(self, equipment_data):
        """Make failure predictions for current equipment state"""
        try:
            import pickle
            
            # Load model
            with open(self.model_path, 'rb') as f:
                model_system = pickle.load(f)
            
            model = model_system['model_info']['model_object']
            features = model_system['model_info']['features']
            
            # Prepare features
            for feature in features:
                if feature not in equipment_data.columns:
                    equipment_data[feature] = 0
            
            X = equipment_data[features].fillna(0)
            predictions = model.predict(X)
            
            # Use existing failure probability if available
            if 'failure_probability_clean' in equipment_data.columns:
                equipment_data['failure_probability'] = equipment_data['failure_probability_clean']
            else:
                equipment_data['failure_probability'] = predictions
            
            return equipment_data
            
        except Exception as e:
            logging.error(f"Error making predictions: {e}")
            return None
    
    def check_alerts(self, equipment_data):
        """Check for equipment that requires alerts"""
        alerts = []
        
        for idx, row in equipment_data.iterrows():
            equipment_id = f"EQ-{idx:03d}"
            failure_prob = row['failure_probability']
            
            alert_level = None
            if failure_prob >= self.alert_thresholds['critical']:
                alert_level = 'critical'
            elif failure_prob >= self.alert_thresholds['high']:
                alert_level = 'high'
            elif failure_prob >= self.alert_thresholds['medium']:
                alert_level = 'medium'
            
            if alert_level:
                alert = {
                    'timestamp': datetime.now().isoformat(),
                    'equipment_id': equipment_id,
                    'equipment_type': row.get('equipment_type', 'Unknown'),
                    'failure_probability': float(failure_prob),
                    'alert_level': alert_level,
                    'location': f"Room-{row.get('room_id', 'Unknown')}",
                    'recommended_action': self._get_recommended_action(alert_level, failure_prob)
                }
                alerts.append(alert)
        
        return alerts
    
    def _get_recommended_action(self, alert_level, failure_prob):
        """Get recommended action based on alert level"""
        if alert_level == 'critical':
            return "IMMEDIATE MAINTENANCE REQUIRED - Stop operation and schedule emergency repair"
        elif alert_level == 'high':
            return "Schedule maintenance within 7 days - Monitor closely"
        elif alert_level == 'medium':
            return "Schedule preventive maintenance within 30 days"
        else:
            return "Continue normal operation"
    
    def send_alerts(self, alerts):
        """Send alerts to maintenance team"""
        for alert in alerts:
            # Check if this equipment has been alerted recently using database
            recent_alerts = self.db.get_active_alerts()
            recent_for_equipment = recent_alerts[
                (recent_alerts['equipment_id'] == alert['equipment_id']) &
                (pd.to_datetime(recent_alerts['created_at']) > datetime.now() - timedelta(hours=6))
            ] if not recent_alerts.empty else pd.DataFrame()
            
            if recent_for_equipment.empty:  # Only send if no recent alert for this equipment
                logging.info(f"ALERT: {alert['alert_level'].upper()} - Equipment {alert['equipment_id']} "
                           f"(Failure Probability: {alert['failure_probability']:.3f})")
                
                # Create alert in database
                alert_data = {
                    'alert_type': alert['alert_level'],
                    'message': f"High failure probability detected: {alert['failure_probability']:.1%}",
                    'severity': alert['alert_level'].lower(),
                    'created_at': datetime.now().isoformat(),
                    'acknowledged': False
                }
                
                self.db.create_alert(alert['equipment_id'], alert_data)
                
                # In production, send email/SMS/webhook notification here
                self._send_notification(alert)
    
    def _send_notification(self, alert):
        """Send notification (placeholder for actual implementation)"""
        # Here you would integrate with your notification system:
        # - Email notifications
        # - SMS alerts
        # - Webhook to maintenance management system
        # - Push notifications to mobile app
        
        notification_message = f"""
EQUIPMENT ALERT - {alert['alert_level'].upper()}

Equipment ID: {alert['equipment_id']}
Type: {alert['equipment_type']}
Location: {alert['location']}
Failure Probability: {alert['failure_probability']:.1%}
Recommended Action: {alert['recommended_action']}

Timestamp: {alert['timestamp']}
        """
        
        # For now, just log the notification
        logging.info(f"Notification sent for {alert['equipment_id']}")
        
        # Save alert to file for dashboard to pick up
        self._save_alert_to_file(alert)
    
    def _save_alert_to_file(self, alert):
        """Save alert to file for dashboard integration"""
        try:
            alert_filename = f"monitoring_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_filename, 'w') as f:
                json.dump(alert, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving alert to file: {e}")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logging.info("Starting monitoring cycle...")
        
        # Load current equipment data
        equipment_data = self.load_current_equipment_data()
        if equipment_data is None:
            logging.error("Failed to load equipment data")
            return
        
        # Make failure predictions
        equipment_data = self.predict_failures(equipment_data)
        if equipment_data is None:
            logging.error("Failed to make predictions")
            return
        
        # Note: Alerts are now only generated when maintenance is scheduled
        # No automatic alert generation during monitoring cycles
        logging.info("Monitoring cycle completed - predictions updated")
        
        # Generate monitoring report
        self.generate_monitoring_report(equipment_data, [])  # Empty alerts list
        
        logging.info("Monitoring cycle completed")
    
    def generate_monitoring_report(self, equipment_data, alerts):
        """Generate monitoring report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_equipment': len(equipment_data),
            'alerts_generated': len(alerts),
            'equipment_by_risk': {
                'critical': len(equipment_data[equipment_data['failure_probability'] >= 0.7]),
                'high': len(equipment_data[equipment_data['failure_probability'] >= 0.5]),
                'medium': len(equipment_data[equipment_data['failure_probability'] >= 0.3]),
                'low': len(equipment_data[equipment_data['failure_probability'] < 0.3])
            },
            'fleet_health_score': float(equipment_data['health_score'].mean()) if 'health_score' in equipment_data.columns else 0,
            'average_failure_probability': float(equipment_data['failure_probability'].mean()),
            'alerts': alerts
        }
        
        # Save report
        report_filename = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            logging.info(f"Monitoring report saved: {report_filename}")
        except Exception as e:
            logging.error(f"Error saving monitoring report: {e}")
    
    def start_continuous_monitoring(self, interval_minutes=60):
        """Start continuous monitoring"""
        self.monitoring_active = True
        logging.info(f"Starting continuous monitoring (interval: {interval_minutes} minutes)")
        
        while self.monitoring_active:
            try:
                self.run_monitoring_cycle()
                
                # Wait for next cycle
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                self.monitoring_active = False
            except Exception as e:
                logging.error(f"Error in monitoring cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logging.info("Monitoring stopped")

def main():
    """Main function for standalone monitoring"""
    monitor = EquipmentMonitor()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Run continuous monitoring
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor.start_continuous_monitoring(interval)
    else:
        # Run single monitoring cycle
        monitor.run_monitoring_cycle()

if __name__ == "__main__":
    main()

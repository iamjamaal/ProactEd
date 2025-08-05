import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class ClassroomEquipmentDataGenerator:
    def __init__(self):
        self.equipment_specs = {
            'projector': {
                'failure_modes': ['lamp_burnout', 'overheating', 'connectivity_loss', 'color_degradation', 'fan_failure'],
                'typical_lifespan_hours': 6000,  # typical projector lamp life
                'high_usage_threshold': 8,  # hours per day
                'normal_temp_range': (35, 45),  # Celsius
                'critical_temp': 65,
                'maintenance_interval_days': 90
            },
            'air_conditioner': {
                'failure_modes': ['compressor_failure', 'refrigerant_leak', 'electrical_fault', 'filter_clog', 'thermostat_malfunction'],
                'typical_lifespan_hours': 15000,  # 10-15 years typical AC life
                'high_usage_threshold': 12,  # hours per day
                'normal_temp_range': (25, 35),  # Celsius
                'critical_temp': 50,
                'maintenance_interval_days': 180
            },
            'podium': {
                'failure_modes': ['microphone_failure', 'speaker_distortion', 'power_supply_issue', 'control_panel_malfunction', 'connectivity_issue'],
                'typical_lifespan_hours': 10000,  # audio equipment typical life
                'high_usage_threshold': 6,  # hours per day
                'normal_temp_range': (20, 30),  # Celsius
                'critical_temp': 40,
                'maintenance_interval_days': 120
            }
        }
        
        # KNUST Academic Calendar (Ghana-based)
        self.academic_calendar = {
            'semester_1': {'start_week': 1, 'end_week': 16, 'usage_multiplier': 1.0},
            'exam_period_1': {'start_week': 15, 'end_week': 16, 'usage_multiplier': 1.5},  # High stress period
            'vacation_1': {'start_week': 17, 'end_week': 20, 'usage_multiplier': 0.1},
            'semester_2': {'start_week': 21, 'end_week': 36, 'usage_multiplier': 1.0},
            'exam_period_2': {'start_week': 35, 'end_week': 36, 'usage_multiplier': 1.5},
            'long_vacation': {'start_week': 37, 'end_week': 52, 'usage_multiplier': 0.2}
        }
        
        # Ghana Climate Patterns
        self.climate_patterns = {
            'harmattan': {'weeks': list(range(1, 9)) + list(range(49, 53)), 'dust_factor': 2.0, 'humidity': 0.3},
            'dry_season': {'weeks': list(range(43, 53)) + list(range(1, 17)), 'dust_factor': 1.5, 'humidity': 0.4},
            'rainy_season': {'weeks': list(range(17, 43)), 'dust_factor': 0.8, 'humidity': 0.8}
        }
        
    def get_academic_usage_multiplier(self, week_of_year):
        """Get usage multiplier based on academic calendar"""
        for period, details in self.academic_calendar.items():
            if details['start_week'] <= week_of_year <= details['end_week']:
                return details['usage_multiplier']
        return 0.5  # Default low usage
    
    def get_climate_factors(self, week_of_year):
        """Get climate factors for given week"""
        dust_factor = 1.0
        humidity = 0.6  # default
        
        for season, details in self.climate_patterns.items():
            if week_of_year in details['weeks']:
                dust_factor = details['dust_factor']
                humidity = details['humidity']
                break
                
        return dust_factor, humidity
    
    def calculate_degradation_score(self, equipment_type, age_months, total_usage_hours, last_maintenance_days):
        """Calculate equipment degradation based on usage and maintenance"""
        specs = self.equipment_specs[equipment_type]
        
        # Age factor (0-1, higher = more degraded)
        age_factor = min(age_months / 60, 1.0)  # Assume 5 years max useful life
        
        # Usage factor
        usage_factor = min(total_usage_hours / specs['typical_lifespan_hours'], 1.0)
        
        # Maintenance factor (lack of maintenance increases degradation)
        maintenance_factor = min(last_maintenance_days / (specs['maintenance_interval_days'] * 2), 1.0)
        
        # Combined degradation score (0-1)
        degradation = (age_factor * 0.3 + usage_factor * 0.5 + maintenance_factor * 0.2)
        return min(degradation, 1.0)
    
    def simulate_sensor_readings(self, equipment_type, degradation_score, daily_usage, dust_factor, humidity, base_temp=28):
        """Simulate realistic sensor readings"""
        specs = self.equipment_specs[equipment_type]
        
        # Operating temperature (increases with degradation and usage)
        temp_baseline = np.random.uniform(*specs['normal_temp_range'])
        temp_increase = degradation_score * 15 + (daily_usage / 12) * 10  # Higher usage = higher temp
        operating_temp = temp_baseline + temp_increase + np.random.normal(0, 2)
        
        # Power consumption (increases with degradation)
        base_power = {'projector': 300, 'air_conditioner': 2000, 'podium': 150}[equipment_type]
        power_consumption = base_power * (1 + degradation_score * 0.3) * np.random.uniform(0.9, 1.1)
        
        # Performance score (decreases with degradation)
        performance_score = (1 - degradation_score) * 100 * np.random.uniform(0.95, 1.0)
        
        # Vibration/noise level (increases with degradation)
        vibration_level = degradation_score * 50 + np.random.uniform(0, 10)
        
        # Environmental factors
        dust_accumulation = dust_factor * degradation_score * 100
        humidity_level = humidity * 100
        
        return {
            'operating_temperature': round(operating_temp, 2),
            'power_consumption': round(power_consumption, 2),
            'performance_score': round(performance_score, 2),
            'vibration_level': round(vibration_level, 2),
            'dust_accumulation': round(dust_accumulation, 2),
            'humidity_level': round(humidity_level, 2)
        }
    
    def calculate_failure_probability(self, equipment_type, degradation_score, operating_temp, days_since_maintenance, is_exam_period=False):
        """Calculate failure probability based on multiple factors"""
        specs = self.equipment_specs[equipment_type]
        
        # Base failure probability from degradation
        base_prob = degradation_score * 0.4
        
        # Temperature factor
        if operating_temp > specs['critical_temp']:
            temp_factor = 0.3
        elif operating_temp > specs['normal_temp_range'][1]:
            temp_factor = 0.1
        else:
            temp_factor = 0.0
        
        # Maintenance factor
        maintenance_factor = min(days_since_maintenance / (specs['maintenance_interval_days'] * 2), 0.2)
        
        # Exam period stress factor
        exam_stress_factor = 0.1 if is_exam_period else 0.0
        
        # Combine factors
        failure_prob = min(base_prob + temp_factor + maintenance_factor + exam_stress_factor, 0.95)
        
        return failure_prob
    
    def determine_failure_type(self, equipment_type, failure_prob):
        """Determine most likely failure type based on probability"""
        if failure_prob < 0.1:
            return 'no_failure'
        
        failure_modes = self.equipment_specs[equipment_type]['failure_modes']
        
        # Weight failure modes based on equipment type and probability
        if equipment_type == 'projector':
            weights = [0.4, 0.25, 0.15, 0.15, 0.05] if failure_prob > 0.5 else [0.2, 0.2, 0.2, 0.2, 0.2]
        elif equipment_type == 'air_conditioner':
            weights = [0.3, 0.2, 0.2, 0.2, 0.1] if failure_prob > 0.5 else [0.2, 0.2, 0.2, 0.2, 0.2]
        else:  # podium
            weights = [0.3, 0.25, 0.2, 0.15, 0.1] if failure_prob > 0.5 else [0.2, 0.2, 0.2, 0.2, 0.2]
        
        return np.random.choice(failure_modes, p=weights)
    
    def generate_dataset(self, n_samples=5000):
        """Generate the complete synthetic dataset"""
        print("Generating synthetic classroom equipment dataset...")
        
        data = []
        
        for i in range(n_samples):
            # Equipment details
            equipment_type = np.random.choice(['projector', 'air_conditioner', 'podium'], 
                                            p=[0.4, 0.35, 0.25])  # More projectors in classrooms
            equipment_id = f"{equipment_type[0].upper()}{i+1000:04d}"
            
            # Room details
            room_types = ['lecture_hall', 'classroom', 'seminar_room', 'lab']
            room_type = np.random.choice(room_types, p=[0.3, 0.4, 0.2, 0.1])
            room_id = f"{room_type.split('_')[0].upper()}{np.random.randint(100, 999)}"
            
            # Time-based features
            current_date = datetime.now() - timedelta(days=np.random.randint(0, 365*2))
            week_of_year = current_date.isocalendar()[1]
            age_months = np.random.randint(1, 60)  # 1-5 years old
            installation_date = current_date - timedelta(days=age_months*30)
            
            # Usage patterns
            academic_multiplier = self.get_academic_usage_multiplier(week_of_year)
            base_daily_usage = np.random.uniform(2, 12)  # Base hours per day
            daily_usage_hours = base_daily_usage * academic_multiplier
            total_usage_hours = daily_usage_hours * age_months * 30 * 0.8  # Account for weekends
            
            # Maintenance history
            last_maintenance_days = np.random.randint(1, 300)
            maintenance_count = max(1, int(age_months / 6))  # Maintenance every 6 months ideally
            
            # Environmental factors
            dust_factor, humidity = self.get_climate_factors(week_of_year)
            room_temperature = np.random.uniform(26, 32)  # Ghana ambient temperature
            
            # Calculate degradation
            degradation_score = self.calculate_degradation_score(
                equipment_type, age_months, total_usage_hours, last_maintenance_days
            )
            
            # Simulate sensor readings
            sensor_data = self.simulate_sensor_readings(
                equipment_type, degradation_score, daily_usage_hours, 
                dust_factor, humidity, room_temperature
            )
            
            # Determine if it's exam period
            is_exam_period = week_of_year in [15, 16, 35, 36]
            
            # Calculate failure probability
            failure_prob = self.calculate_failure_probability(
                equipment_type, degradation_score, sensor_data['operating_temperature'],
                last_maintenance_days, is_exam_period
            )
            
            # Determine failure type and urgency
            failure_type = self.determine_failure_type(equipment_type, failure_prob)
            
            # Maintenance urgency
            if failure_prob >= 0.7:
                maintenance_urgency = 'critical'
            elif failure_prob >= 0.4:
                maintenance_urgency = 'high'
            elif failure_prob >= 0.2:
                maintenance_urgency = 'medium'
            else:
                maintenance_urgency = 'low'
            
            # Days to failure estimation
            if failure_prob > 0.1:
                days_to_failure = max(1, int((1 - failure_prob) * 90))
            else:
                days_to_failure = np.random.randint(90, 365)
            
            # Compile record
            record = {
                # Equipment identification
                'equipment_id': equipment_id,
                'equipment_type': equipment_type,
                'room_id': room_id,
                'room_type': room_type,
                'installation_date': installation_date.strftime('%Y-%m-%d'),
                'age_months': age_months,
                
                # Academic context
                'week_of_year': week_of_year,
                'is_exam_period': is_exam_period,
                'academic_usage_multiplier': round(academic_multiplier, 2),
                'daily_usage_hours': round(daily_usage_hours, 2),
                'total_usage_hours': round(total_usage_hours, 2),
                
                # Maintenance history
                'last_maintenance_days': last_maintenance_days,
                'maintenance_count': maintenance_count,
                'degradation_score': round(degradation_score, 3),
                
                # Environmental factors
                'room_temperature': round(room_temperature, 2),
                'dust_factor': round(dust_factor, 2),
                'humidity': round(humidity, 2),
                
                # Sensor readings
                **sensor_data,
                
                # Target variables
                'failure_probability': round(failure_prob, 3),
                'failure_type': failure_type,
                'maintenance_urgency': maintenance_urgency,
                'days_to_failure': days_to_failure,
                'equipment_status': 'operational' if failure_prob < 0.5 else 'at_risk'
            }
            
            data.append(record)
            
            if (i + 1) % 1000 == 0:
                print(f"Generated {i + 1} records...")
        
        df = pd.DataFrame(data)
        print(f"\nDataset generation complete! Shape: {df.shape}")
        
        # Display basic statistics
        print("\nEquipment Type Distribution:")
        print(df['equipment_type'].value_counts())
        
        print("\nMaintenance Urgency Distribution:")
        print(df['maintenance_urgency'].value_counts())
        
        print("\nFailure Probability Statistics:")
        print(df['failure_probability'].describe())
        
        return df

# Generate the dataset
generator = ClassroomEquipmentDataGenerator()
classroom_dataset = generator.generate_dataset(n_samples=5000)

# Save to CSV
classroom_dataset.to_csv('knust_classroom_equipment_dataset.csv', index=False)
print("\nDataset saved as 'knust_classroom_equipment_dataset.csv'")

# Display sample data
print("\nSample Data:")
print(classroom_dataset.head())

# Additional analysis
print("\nDataset Info:")
print(classroom_dataset.info())

print("\nCorrelation between key features:")
numeric_cols = ['age_months', 'daily_usage_hours', 'total_usage_hours', 'last_maintenance_days', 
                'degradation_score', 'operating_temperature', 'failure_probability']
correlation_matrix = classroom_dataset[numeric_cols].corr()
print(correlation_matrix['failure_probability'].sort_values(ascending=False))





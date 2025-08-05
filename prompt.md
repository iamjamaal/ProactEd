# GitHub Copilot Prompt for ProactED Machine Learning Implementation

## Project Overview
I'm building **ProactED**, a predictive maintenance system for classroom equipment (projectors, air conditioners, podiums) at KNUST. I have a synthetic dataset with 5000+ records containing equipment sensor data, academic calendar integration, and Ghana-specific environmental factors.

## Dataset Structure
My dataset (`knust_classroom_equipment_dataset.csv`) contains:

### Equipment Features:
- `equipment_type`: projector, air_conditioner, podium
- `equipment_id`, `room_id`, `room_type`, `age_months`
- `installation_date`, `maintenance_count`, `last_maintenance_days`

### Academic Context Features:
- `week_of_year`, `is_exam_period`, `academic_usage_multiplier`
- `daily_usage_hours`, `total_usage_hours`

### Environmental Features (Ghana-specific):
- `room_temperature`, `dust_factor`, `humidity`, `season`
- `dust_accumulation`, `operating_temperature`

### Sensor Data:
- `power_consumption`, `performance_score`, `vibration_level`
- `degradation_score`

### Target Variables:
- `failure_probability` (0-1): Primary prediction target
- `maintenance_urgency`: critical, high, medium, low
- `days_to_failure`: Estimated days until failure
- `failure_type`: Equipment-specific failure modes

## Implementation Tasks

### 1. Data Preprocessing Pipeline
```python
# Help me create a comprehensive preprocessing pipeline that:
# - Handles the academic calendar features properly
# - Creates time-based features for equipment lifecycle
# - Engineers domain-specific features for classroom equipment
# - Handles categorical encoding for equipment types and room types
# - Scales numerical features appropriately
# - Creates interaction features between usage patterns and environmental factors
# - Implements data validation specific to educational equipment
```

### 2. Multi-Target Prediction Models
```python
# Implement ensemble models for multiple prediction tasks:

# PRIMARY MODEL: Failure Probability Prediction (Regression 0-1)
# - Use Random Forest, XGBoost, and Neural Network ensemble
# - Custom loss function that weighs exam period predictions higher
# - Feature importance analysis for maintenance decision support

# SECONDARY MODEL: Maintenance Urgency Classification
# - Multi-class classifier: critical, high, medium, low
# - Class balancing techniques for imbalanced urgency levels
# - Precision-focused for critical/high classes to avoid false negatives

# TERTIARY MODEL: Days-to-Failure Estimation (Regression)
# - Time-series aware model considering equipment degradation curves
# - Integration with academic calendar for maintenance scheduling
# - Confidence intervals for prediction uncertainty
```

### 3. Equipment-Specific Model Architecture
```python
# Create specialized models for each equipment type:

# PROJECTOR MODEL:
# - Focus on lamp_hours, operating_temperature, dust_accumulation
# - Special handling for overheating patterns
# - Color degradation prediction based on usage intensity

# AIR CONDITIONER MODEL:
# - Emphasize power_consumption, room_temperature, humidity
# - Seasonal pattern recognition for Ghana climate
# - Compressor failure prediction using vibration patterns

# PODIUM MODEL:
# - Audio performance degradation modeling
# - Connection stability prediction
# - Usage pattern analysis for lecture halls vs classrooms
```

### 4. Academic Calendar Integration
```python
# Implement smart scheduling features:
# - Maintenance window optimization avoiding exam periods (weeks 15-16, 35-36)
# - Priority escalation during high-usage academic periods
# - Semester break bulk maintenance scheduling
# - Equipment criticality weighting based on room importance
# - Integration with KNUST academic calendar API (if available)
```

### 5. Real-time Prediction API for ASP.NET Core
```csharp
// Create production-ready API endpoints:

// POST /api/ml/predict-failure
// Input: equipment_id, current_sensor_readings
// Output: failure_probability, confidence_score, time_to_failure

// POST /api/ml/batch-predict
// Input: List of equipment with sensor data
// Output: Batch predictions with maintenance priorities

// GET /api/ml/maintenance-schedule
// Input: date_range, equipment_types[], room_ids[]
// Output: Optimized maintenance schedule avoiding academic conflicts

// POST /api/ml/update-model
// Input: new_maintenance_data, feedback_data
// Output: Model retraining status and performance metrics

// GET /api/ml/equipment-health-dashboard
// Input: equipment_filters
// Output: Real-time health scores and alerts for dashboard
```

### 6. Feature Engineering for Educational Context
```python
# Create education-specific features:

# USAGE INTENSITY FEATURES:
# - lecture_hours_per_week, student_capacity_utilization
# - peak_usage_stress_score, weekend_rest_periods
# - exam_period_overload_factor

# ENVIRONMENTAL DEGRADATION:
# - harmattan_dust_exposure_score (Dec-Feb Ghana season)
# - rainy_season_humidity_damage (Apr-Sep Ghana season)  
# - classroom_ventilation_adequacy_score

# MAINTENANCE OPTIMIZATION:
# - optimal_maintenance_window_score
# - resource_availability_alignment
# - cost_benefit_maintenance_timing
```

### 7. Model Evaluation & Validation
```python
# Implement comprehensive evaluation:

# BUSINESS METRICS:
# - Academic_Disruption_Score = failure_prob × class_schedule_impact
# - Maintenance_Cost_Efficiency = prevented_emergency_repairs / scheduled_maintenance_cost
# - Equipment_Uptime_During_Critical_Periods (exam weeks)

# TECHNICAL METRICS:
# - Time-series cross-validation respecting academic calendar
# - Equipment-type stratified validation
# - Prediction confidence calibration
# - Model fairness across different room types and equipment ages

# CUSTOM LOSS FUNCTIONS:
# - Higher penalty for false negatives during exam periods
# - Cost-sensitive learning based on equipment replacement costs
# - Multi-objective optimization balancing accuracy vs maintenance cost
```

### 8. MLOps Pipeline for Production
```python
# Build production ML pipeline:

# MODEL MONITORING:
# - Prediction drift detection for equipment degradation patterns
# - Performance monitoring during different academic periods
# - Automated alerts when model accuracy drops below threshold

# AUTOMATED RETRAINING:
# - Incremental learning with new maintenance records
# - Seasonal model updates for Ghana climate patterns
# - A/B testing framework for model improvements

# DATA PIPELINE:
# - Real-time sensor data ingestion and preprocessing
# - Data quality monitoring and anomaly detection
# - Feature store for consistent feature engineering
```

### 9. Integration with ProactED Web Application
```csharp
// ASP.NET Core 9.0 integration components:

// ENTITY FRAMEWORK MODELS:
public class EquipmentPrediction
{
    public int Id { get; set; }
    public string EquipmentId { get; set; }
    public DateTime PredictionDate { get; set; }
    public double FailureProbability { get; set; }
    public string MaintenanceUrgency { get; set; }
    public int DaysToFailure { get; set; }
    public double ConfidenceScore { get; set; }
    // Academic context
    public bool IsExamPeriod { get; set; }
    public int WeekOfYear { get; set; }
}

// BACKGROUND SERVICES:
// - Scheduled prediction updates every 6 hours
// - Alert generation for critical equipment
// - Maintenance schedule optimization
// - Model performance monitoring

// DASHBOARD CONTROLLERS:
// - Real-time equipment health status
// - Predictive maintenance calendar
// - Cost savings analytics
// - Equipment lifecycle insights
```

### 10. Advanced Analytics Features
```python
# Implement sophisticated analytics:

# EQUIPMENT LIFECYCLE MANAGEMENT:
# - Remaining useful life estimation
# - Optimal replacement timing prediction
# - Total cost of ownership optimization

# RESOURCE OPTIMIZATION:
# - Maintenance team workload balancing
# - Spare parts inventory optimization
# - Energy consumption prediction and optimization

# PREDICTIVE INSIGHTS:
# - Failure pattern analysis across similar equipment
# - Seasonal maintenance planning recommendations
# - Budget forecasting for maintenance and replacements
```

## Business Requirements

### Critical Success Metrics:
1. **>85% accuracy** in predicting failures 7-14 days in advance
2. **Zero critical equipment failures** during exam periods
3. **30% reduction** in emergency maintenance calls
4. **20% cost savings** through optimized maintenance scheduling
5. **Real-time alerts** within 15 minutes of sensor data changes

### Academic Integration Requirements:
- **Never schedule maintenance** during exam weeks (15-16, 35-36)
- **Prioritize high-capacity rooms** (lecture halls > classrooms > labs)
- **Align maintenance** with academic calendar breaks
- **Escalate alerts** during high-usage periods

### Ghana-Specific Considerations:
- **Harmattan season impact** (Dec-Feb): increased dust, filter clogging
- **Power grid instability**: factor in electrical fault probabilities
- **Tropical humidity**: accelerated corrosion and electrical issues
- **Resource constraints**: optimize for local technician skills and parts availability

## Expected Deliverables:
1. **Production-ready ML models** with >85% accuracy
2. **RESTful API endpoints** for real-time predictions
3. **Background processing services** for batch predictions
4. **Interactive dashboard components** for maintenance managers
5. **Automated alert system** with SMS/email integration
6. **Comprehensive documentation** and deployment guides
7. **Unit and integration tests** for all ML components

## Technology Stack:
- **ML Framework**: Scikit-learn, XGBoost, TensorFlow/Keras
- **Backend**: ASP.NET Core 9.0, Entity Framework Core
- **Database**: SQL Server for predictions storage
- **Caching**: Redis for real-time predictions
- **Monitoring**: Application Insights, custom dashboards
- **Deployment**: Docker containers, Azure/AWS deployment

Please help me implement this step-by-step, starting with the data preprocessing pipeline and feature engineering specifically designed for classroom equipment in an educational environment. Focus on creating a solution that truly understands the academic context and Ghana-specific environmental factors.

The goal is to create a system that not only predicts equipment failures but does so in a way that minimizes disruption to KNUST's academic mission while optimizing maintenance resources and costs.
# EQUIPMENT SUMMARY LOGIC IMPROVEMENTS

## Current Flaws and Proposed Solutions:

### 1. DATA CONSISTENCY ISSUES
**Current Problem:**
```python
'location': f"Facility-{np.random.choice(['A', 'B', 'C'])}-Zone-{np.random.randint(1, 5)}"
```

**Fix:**
```python
def get_consistent_equipment_data(equipment_id):
    # Use equipment_id as seed for consistent data
    np.random.seed(hash(equipment_id) % 2**32)
    location = f"Facility-{np.random.choice(['A', 'B', 'C'])}-Zone-{np.random.randint(1, 5)}"
    # Reset seed after use
    np.random.seed(None)
    return location
```

### 2. OPERATIONAL STATUS LOGIC
**Current Problem:**
```python
'operational_status': 'Running' if equipment_row['failure_probability'] < 0.8 else 'Requires Attention'
```

**Fix:**
```python
def determine_operational_status(failure_prob, last_maintenance, sensor_readings):
    if failure_prob >= 0.9:
        return "🔴 CRITICAL - Stop Operation"
    elif failure_prob >= 0.7:
        return "🟠 WARNING - Schedule Immediate Maintenance"
    elif failure_prob >= 0.5:
        return "🟡 CAUTION - Monitor Closely"
    elif last_maintenance > 365:
        return "🔵 MAINTENANCE OVERDUE"
    else:
        return "🟢 OPERATIONAL"
```

### 3. MAINTENANCE SCHEDULING
**Current Problem:**
```python
'next_scheduled': 'Overdue' if last_maintenance > 180 else f"{180 - last_maintenance} days"
```

**Fix:**
```python
MAINTENANCE_INTERVALS = {
    'HVAC': 90,      # Every 3 months
    'Projector': 180, # Every 6 months  
    'Computer': 365,  # Annual
    'Whiteboard': 730, # Every 2 years
    'default': 180
}

def calculate_next_maintenance(equipment_type, last_maintenance):
    interval = MAINTENANCE_INTERVALS.get(equipment_type, MAINTENANCE_INTERVALS['default'])
    days_remaining = interval - last_maintenance
    
    if days_remaining <= 0:
        return f"OVERDUE by {abs(days_remaining)} days"
    elif days_remaining <= 30:
        return f"DUE in {days_remaining} days"
    else:
        return f"Next: {days_remaining} days"
```

### 4. ISSUE COMPLEXITY PRIORITIZATION
**Current Problem:**
```python
# Later conditions overwrite higher priority issues
if prob >= 0.8:
    complexity = 'critical'
# ...later...
if vib > 5:
    complexity = 'high'  # Overwrites critical!
```

**Fix:**
```python
def determine_complexity_priority(issues_detected):
    complexity_scores = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    max_complexity = 'low'
    for issue in issues_detected:
        if issue['complexity_score'] > complexity_scores[max_complexity]:
            max_complexity = issue['complexity']
    
    return max_complexity
```

### 5. EQUIPMENT-SPECIFIC THRESHOLDS
**Current Problem:**
```python
if temp > 95:  # Same threshold for all equipment
```

**Fix:**
```python
EQUIPMENT_THRESHOLDS = {
    'HVAC': {'temp_critical': 85, 'temp_warning': 75, 'vibration_max': 2.0},
    'Projector': {'temp_critical': 95, 'temp_warning': 85, 'vibration_max': 1.0},
    'Computer': {'temp_critical': 80, 'temp_warning': 70, 'vibration_max': 0.5},
    'default': {'temp_critical': 95, 'temp_warning': 85, 'vibration_max': 3.0}
}

def get_equipment_thresholds(equipment_type):
    return EQUIPMENT_THRESHOLDS.get(equipment_type, EQUIPMENT_THRESHOLDS['default'])
```

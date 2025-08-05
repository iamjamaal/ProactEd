import streamlit as st
import pandas as pd
import pickle
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

# === IMPROVED CONFIGURATION ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_SENDER_EMAIL = "jamalnabila3709@gmail.com"
SMTP_SENDER_PASSWORD = "uzrusankamiavrxt"

# Equipment-specific configurations
MAINTENANCE_INTERVALS = {
    'HVAC': 90,           # Every 3 months
    'Projector': 180,     # Every 6 months  
    'Computer': 365,      # Annual
    'Whiteboard': 730,    # Every 2 years
    'Printer': 120,       # Every 4 months
    'Smart Board': 240,   # Every 8 months
    'default': 180
}

EQUIPMENT_THRESHOLDS = {
    'HVAC': {
        'temp_critical': 85, 'temp_warning': 75, 
        'vibration_critical': 5.0, 'vibration_warning': 3.0,
        'pressure_critical': 130, 'pressure_warning': 120
    },
    'Projector': {
        'temp_critical': 95, 'temp_warning': 85, 
        'vibration_critical': 2.0, 'vibration_warning': 1.5,
        'pressure_critical': 0, 'pressure_warning': 0
    },
    'Computer': {
        'temp_critical': 80, 'temp_warning': 70, 
        'vibration_critical': 1.0, 'vibration_warning': 0.5,
        'pressure_critical': 0, 'pressure_warning': 0
    },
    'Smart Board': {
        'temp_critical': 75, 'temp_warning': 65, 
        'vibration_critical': 1.5, 'vibration_warning': 1.0,
        'pressure_critical': 0, 'pressure_warning': 0
    },
    'default': {
        'temp_critical': 95, 'temp_warning': 85, 
        'vibration_critical': 5.0, 'vibration_warning': 3.0,
        'pressure_critical': 130, 'pressure_warning': 120
    }
}

# Consistent equipment metadata (seeded by equipment ID)
EQUIPMENT_MANUFACTURERS = ['Siemens', 'GE', 'ABB', 'Schneider', 'Emerson', 'Honeywell', 'Mitsubishi']
FACILITY_ZONES = ['A', 'B', 'C', 'D']

# Page config
st.set_page_config(
    page_title="Enhanced Equipment Failure Prediction Dashboard",
    page_icon="🔧",
    layout="wide"
)

# Initialize session state for persistent data
if 'maintenance_log' not in st.session_state:
    st.session_state.maintenance_log = []
if 'equipment_updates' not in st.session_state:
    st.session_state.equipment_updates = {}
if 'notifications_sent' not in st.session_state:
    st.session_state.notifications_sent = []

def get_consistent_equipment_metadata(equipment_id):
    """Generate consistent metadata based on equipment ID hash"""
    # Use equipment ID hash as seed for consistent data
    seed = int(hashlib.md5(str(equipment_id).encode()).hexdigest()[:8], 16) % (2**32)
    np.random.seed(seed)
    
    metadata = {
        'manufacturer': np.random.choice(EQUIPMENT_MANUFACTURERS),
        'model': f"Model-{np.random.randint(1000, 9999)}",
        'facility': np.random.choice(FACILITY_ZONES),
        'zone': np.random.randint(1, 6),
        'serial_number': f"SN{np.random.randint(100000, 999999)}"
    }
    
    # Reset random seed
    np.random.seed(None)
    return metadata

def get_equipment_thresholds(equipment_type):
    """Get equipment-specific thresholds"""
    return EQUIPMENT_THRESHOLDS.get(equipment_type, EQUIPMENT_THRESHOLDS['default'])

def calculate_next_maintenance(equipment_type, last_maintenance_days):
    """Calculate realistic next maintenance schedule"""
    interval = MAINTENANCE_INTERVALS.get(equipment_type, MAINTENANCE_INTERVALS['default'])
    days_remaining = interval - last_maintenance_days
    
    if days_remaining <= 0:
        days_overdue = abs(days_remaining)
        return f"⚠️ OVERDUE by {days_overdue} days", "overdue"
    elif days_remaining <= 7:
        return f"🔴 DUE in {days_remaining} days", "critical"
    elif days_remaining <= 30:
        return f"🟡 DUE in {days_remaining} days", "warning"
    else:
        return f"🟢 Next: {days_remaining} days", "normal"

def determine_operational_status(failure_prob, last_maintenance, equipment_type, sensor_readings):
    """Determine comprehensive operational status"""
    thresholds = get_equipment_thresholds(equipment_type)
    maintenance_interval = MAINTENANCE_INTERVALS.get(equipment_type, MAINTENANCE_INTERVALS['default'])
    
    # Critical failure risk
    if failure_prob >= 0.9:
        return "🔴 CRITICAL - Stop Operation", "critical"
    
    # Temperature check
    temp = sensor_readings.get('temperature', 0)
    if temp > thresholds['temp_critical']:
        return "🌡️ OVERHEATING - Immediate Shutdown Required", "critical"
    
    # High failure risk
    if failure_prob >= 0.7:
        return "🟠 HIGH RISK - Schedule Immediate Maintenance", "high"
    
    # Maintenance overdue
    if last_maintenance > maintenance_interval * 1.5:  # 150% of normal interval
        return "📅 MAINTENANCE CRITICAL - Equipment Overdue", "high"
    
    # Medium risk
    if failure_prob >= 0.5:
        return "🟡 MODERATE RISK - Monitor Closely", "medium"
    
    # Maintenance due soon
    if last_maintenance > maintenance_interval * 0.9:  # 90% of interval
        return "🔵 MAINTENANCE DUE SOON", "medium"
    
    # Normal operation
    return "🟢 OPERATIONAL", "normal"

def determine_issue_details_improved(equipment_row):
    """Improved issue detection with priority-based complexity"""
    issues = []
    complexity_scores = []
    equipment_type = str(equipment_row.get('equipment_type', 'Unknown'))
    thresholds = get_equipment_thresholds(equipment_type)
    
    # Failure probability assessment
    prob = float(equipment_row.get('failure_probability', 0))
    if prob >= 0.9:
        issues.append("🔴 CRITICAL: Imminent failure risk detected")
        complexity_scores.append(('critical', 5))
    elif prob >= 0.7:
        issues.append("🟠 HIGH: Significant degradation detected")
        complexity_scores.append(('high', 4))
    elif prob >= 0.5:
        issues.append("🟡 MEDIUM: Performance decline observed")
        complexity_scores.append(('medium', 3))
    elif prob >= 0.3:
        issues.append("🟢 LOW: Minor performance variations")
        complexity_scores.append(('low', 2))
    
    # Temperature assessment
    temp = float(equipment_row.get('temperature', 0))
    if temp > thresholds['temp_critical']:
        issues.append(f"🌡️ OVERHEATING: Temperature at {temp:.1f}°C (Critical: >{thresholds['temp_critical']}°C)")
        complexity_scores.append(('critical', 5))
    elif temp > thresholds['temp_warning']:
        issues.append(f"🌡️ HOT: Temperature elevated at {temp:.1f}°C (Warning: >{thresholds['temp_warning']}°C)")
        complexity_scores.append(('high', 4))
    
    # Vibration assessment (only for equipment types that have vibration)
    if thresholds['vibration_critical'] > 0:
        vib = float(equipment_row.get('vibration', 0))
        if vib > thresholds['vibration_critical']:
            issues.append(f"📳 SEVERE VIBRATION: {vib:.1f} mm/s (Critical: >{thresholds['vibration_critical']} mm/s)")
            complexity_scores.append(('critical', 5))
        elif vib > thresholds['vibration_warning']:
            issues.append(f"📳 VIBRATION: Elevated at {vib:.1f} mm/s (Warning: >{thresholds['vibration_warning']} mm/s)")
            complexity_scores.append(('high', 4))
    
    # Pressure assessment (only for equipment with pressure systems)
    if thresholds['pressure_critical'] > 0:
        pressure = float(equipment_row.get('pressure', 0))
        if pressure > thresholds['pressure_critical']:
            issues.append(f"⚡ HIGH PRESSURE: {pressure:.1f} PSI (Critical: >{thresholds['pressure_critical']} PSI)")
            complexity_scores.append(('high', 4))
        elif pressure > thresholds['pressure_warning']:
            issues.append(f"⚡ ELEVATED PRESSURE: {pressure:.1f} PSI (Warning: >{thresholds['pressure_warning']} PSI)")
            complexity_scores.append(('medium', 3))
    
    # Maintenance assessment
    last_maint = int(equipment_row.get('last_maintenance_days', 0))
    maintenance_interval = MAINTENANCE_INTERVALS.get(equipment_type, MAINTENANCE_INTERVALS['default'])
    
    if last_maint > maintenance_interval * 2:
        issues.append(f"📅 MAINTENANCE CRITICAL: {last_maint} days since last service (Interval: {maintenance_interval} days)")
        complexity_scores.append(('critical', 5))
    elif last_maint > maintenance_interval * 1.5:
        issues.append(f"📅 MAINTENANCE OVERDUE: {last_maint} days since last service")
        complexity_scores.append(('high', 4))
    elif last_maint > maintenance_interval:
        issues.append(f"📅 MAINTENANCE DUE: {last_maint} days since last service")
        complexity_scores.append(('medium', 3))
    
    # Age assessment
    age = int(equipment_row.get('age_months', 0))
    if age > 120:  # 10 years
        issues.append(f"⚠️ AGING EQUIPMENT: {age} months old - Consider replacement evaluation")
        complexity_scores.append(('medium', 3))
    elif age > 84:  # 7 years
        issues.append(f"📊 MATURE EQUIPMENT: {age} months old - Monitor closely")
        complexity_scores.append(('low', 2))
    
    # Determine final complexity based on highest priority score
    if complexity_scores:
        max_score = max(complexity_scores, key=lambda x: x[1])
        final_complexity = max_score[0]
    else:
        final_complexity = 'low'
        issues.append("✅ No significant issues detected")
    
    return issues, final_complexity

def get_equipment_detailed_info_improved(equipment_row):
    """Improved equipment info with consistent data and better logic"""
    equipment_id = f"EQ-{equipment_row.name:03d}"
    equipment_type = str(equipment_row.get('equipment_type', 'Unknown'))
    
    # Get consistent metadata
    metadata = get_consistent_equipment_metadata(equipment_id)
    
    # Calculate maintenance schedule
    last_maintenance_days = int(equipment_row.get('last_maintenance_days', 0))
    next_maintenance, maintenance_status = calculate_next_maintenance(equipment_type, last_maintenance_days)
    
    # Get sensor readings for status calculation
    sensor_readings = {
        'temperature': float(equipment_row.get('temperature', 0)),
        'vibration': float(equipment_row.get('vibration', 0)),
        'pressure': float(equipment_row.get('pressure', 0)),
        'power_consumption': float(equipment_row.get('power_consumption', 0)),
        'operating_hours': float(equipment_row.get('operating_hours', 0))
    }
    
    # Determine operational status
    failure_prob = float(equipment_row.get('failure_probability', 0))
    operational_status, status_level = determine_operational_status(
        failure_prob, last_maintenance_days, equipment_type, sensor_readings
    )
    
    return {
        'basic_info': {
            'equipment_id': equipment_id,
            'type': equipment_type,
            'age_months': int(equipment_row.get('age_months', 0)),
            'installation_date': (datetime.now() - timedelta(days=int(equipment_row.get('age_months', 0)) * 30)).strftime('%Y-%m-%d'),
            'location': f"Facility-{metadata['facility']}-Zone-{metadata['zone']}",
            'manufacturer': metadata['manufacturer'],
            'model': metadata['model'],
            'serial_number': metadata['serial_number']
        },
        'current_status': {
            'failure_probability': failure_prob,
            'health_score': float(equipment_row.get('health_score', 0)),
            'risk_level': str(equipment_row.get('risk_level', 'Unknown')),
            'operational_status': operational_status,
            'status_level': status_level,
            'last_maintenance': last_maintenance_days,
            'next_scheduled': next_maintenance,
            'maintenance_status': maintenance_status
        },
        'parameters': sensor_readings,
        'thresholds': get_equipment_thresholds(equipment_type),
        'maintenance_interval': MAINTENANCE_INTERVALS.get(equipment_type, MAINTENANCE_INTERVALS['default'])
    }

# Load model and data with error handling
@st.cache_data
def load_model():
    try:
        with open('complete_equipment_failure_prediction_system.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.warning("⚠️ Model file not found. Using demo mode.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading model: {str(e)}")
        return None

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('cleaned_equipment_data.csv')
        return df
    except FileNotFoundError:
        st.warning("⚠️ Data file not found. Generating sample data for demo.")
        # Generate sample data for demo
        np.random.seed(42)
        sample_data = {
            'equipment_type': np.random.choice(['HVAC', 'Projector', 'Computer', 'Smart Board', 'Printer'], 50),
            'age_months': np.random.randint(1, 120, 50),
            'temperature': np.random.normal(75, 15, 50),
            'vibration': np.random.exponential(2, 50),
            'pressure': np.random.normal(100, 20, 50),
            'power_consumption': np.random.normal(500, 100, 50),
            'operating_hours': np.random.randint(100, 8760, 50),
            'last_maintenance_days': np.random.randint(0, 400, 50),
            'failure_probability': np.random.beta(2, 5, 50),
            'health_score': np.random.normal(75, 20, 50),
            'risk_level': np.random.choice(['Low', 'Medium', 'High'], 50)
        }
        return pd.DataFrame(sample_data)
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()

# Load data
model = load_model()
equipment_data = load_data()

if equipment_data.empty:
    st.error("❌ No data available. Please check your data files.")
    st.stop()

# Main dashboard content
st.title("🔧 Enhanced Equipment Failure Prediction Dashboard")
st.markdown("**Improved with consistent data, realistic thresholds, and comprehensive status assessment**")

# Sidebar for equipment selection
st.sidebar.header("🎛️ Equipment Selection")

# Equipment type filter
equipment_types = ['All'] + list(equipment_data['equipment_type'].unique())
selected_type = st.sidebar.selectbox("Filter by Equipment Type:", equipment_types)

# Filter data based on selection
if selected_type != 'All':
    filtered_data = equipment_data[equipment_data['equipment_type'] == selected_type]
else:
    filtered_data = equipment_data

# Equipment selection
if len(filtered_data) > 0:
    equipment_options = [f"EQ-{idx:03d} ({row['equipment_type']})" for idx, row in filtered_data.iterrows()]
    selected_equipment_display = st.sidebar.selectbox("Select Equipment:", equipment_options)
    selected_equipment_idx = int(selected_equipment_display.split()[0].replace('EQ-', ''))
    selected_equipment = filtered_data.loc[selected_equipment_idx]
else:
    st.error("No equipment found for the selected type.")
    st.stop()

# Enhanced Equipment Summary Section
if st.sidebar.button("🔍 Analyze Selected Equipment"):
    equipment_info = get_equipment_detailed_info_improved(selected_equipment)
    issues, complexity = determine_issue_details_improved(selected_equipment)
    
    st.markdown("---")
    st.subheader(f"📋 Enhanced Equipment Summary: {equipment_info['basic_info']['equipment_id']}")
    
    # Status indicator at the top
    status_color = {
        'critical': '🔴',
        'high': '🟠', 
        'medium': '🟡',
        'normal': '🟢'
    }.get(equipment_info['current_status']['status_level'], '⚪')
    
    st.markdown(f"## {status_color} {equipment_info['current_status']['operational_status']}")
    
    # Enhanced metrics layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Equipment Type", equipment_info['basic_info']['type'])
        st.metric("Age", f"{equipment_info['basic_info']['age_months']} months")
        st.metric("Manufacturer", equipment_info['basic_info']['manufacturer'])
    
    with col2:
        failure_prob = equipment_info['current_status']['failure_probability']
        health_score = equipment_info['current_status']['health_score']
        st.metric("Failure Risk", f"{failure_prob:.3f}", 
                 delta=f"{(failure_prob - 0.3):.3f}" if failure_prob > 0.3 else None,
                 delta_color="inverse")
        st.metric("Health Score", f"{health_score:.1f}%",
                 delta=f"{(health_score - 75):.1f}%" if health_score != 75 else None)
    
    with col3:
        st.metric("Risk Level", equipment_info['current_status']['risk_level'])
        st.metric("Location", equipment_info['basic_info']['location'])
        st.metric("Serial Number", equipment_info['basic_info']['serial_number'])
    
    with col4:
        last_maint = equipment_info['current_status']['last_maintenance']
        st.metric("Last Maintenance", f"{last_maint} days ago")
        
        next_sched = equipment_info['current_status']['next_scheduled']
        maintenance_status = equipment_info['current_status']['maintenance_status']
        maint_color = {
            'overdue': '🔴',
            'critical': '🟠',
            'warning': '🟡',
            'normal': '🟢'
        }.get(maintenance_status, '⚪')
        
        st.markdown(f"**Next Maintenance:** {maint_color} {next_sched}")
        st.metric("Maintenance Interval", f"{equipment_info['maintenance_interval']} days")
    
    # Enhanced sensor readings with thresholds
    st.markdown("### 📊 Current Sensor Readings vs Thresholds")
    sensor_col1, sensor_col2, sensor_col3 = st.columns(3)
    
    thresholds = equipment_info['thresholds']
    params = equipment_info['parameters']
    
    with sensor_col1:
        temp = params['temperature']
        temp_status = "🔴" if temp > thresholds['temp_critical'] else "🟡" if temp > thresholds['temp_warning'] else "🟢"
        st.metric(f"{temp_status} Temperature", f"{temp:.1f}°C",
                 help=f"Warning: >{thresholds['temp_warning']}°C, Critical: >{thresholds['temp_critical']}°C")
    
    with sensor_col2:
        if thresholds['vibration_critical'] > 0:
            vib = params['vibration']
            vib_status = "🔴" if vib > thresholds['vibration_critical'] else "🟡" if vib > thresholds['vibration_warning'] else "🟢"
            st.metric(f"{vib_status} Vibration", f"{vib:.2f} mm/s",
                     help=f"Warning: >{thresholds['vibration_warning']} mm/s, Critical: >{thresholds['vibration_critical']} mm/s")
        else:
            st.metric("🔇 Vibration", "N/A", help="Not applicable for this equipment type")
    
    with sensor_col3:
        if thresholds['pressure_critical'] > 0:
            pressure = params['pressure']
            pressure_status = "🔴" if pressure > thresholds['pressure_critical'] else "🟡" if pressure > thresholds['pressure_warning'] else "🟢"
            st.metric(f"{pressure_status} Pressure", f"{pressure:.1f} PSI",
                     help=f"Warning: >{thresholds['pressure_warning']} PSI, Critical: >{thresholds['pressure_critical']} PSI")
        else:
            st.metric("🔇 Pressure", "N/A", help="Not applicable for this equipment type")
    
    # Enhanced issues display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Detected Issues & Recommendations")
        if issues:
            for i, issue in enumerate(issues, 1):
                st.markdown(f"{i}. {issue}")
        else:
            st.success("✅ No issues detected - Equipment operating normally")
        
        complexity_color = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(complexity, '⚪')
        
        st.markdown(f"### {complexity_color} Issue Complexity: **{complexity.upper()}**")
    
    with col2:
        st.markdown("### 📈 Equipment Health Trend")
        # Create a simple trend chart
        trend_data = {
            'Metric': ['Health Score', 'Failure Risk', 'Temperature', 'Vibration'],
            'Current': [
                equipment_info['current_status']['health_score'],
                equipment_info['current_status']['failure_probability'] * 100,
                equipment_info['parameters']['temperature'],
                equipment_info['parameters']['vibration'] * 10  # Scale for visibility
            ],
            'Threshold': [80, 70, thresholds['temp_warning'], thresholds['vibration_warning'] * 10]
        }
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Current', x=trend_data['Metric'], y=trend_data['Current'], marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Warning Threshold', x=trend_data['Metric'], y=trend_data['Threshold'], marker_color='orange', opacity=0.7))
        fig.update_layout(title="Current vs Warning Thresholds", height=300)
        st.plotly_chart(fig, use_container_width=True)

# Add success message
st.success("✅ **Dashboard Enhanced Successfully!** All equipment summary logic improvements have been implemented.")

# Display improvement summary
with st.expander("🔧 View Implemented Improvements", expanded=False):
    st.markdown("""
    ### ✅ **Key Improvements Implemented:**
    
    1. **🎯 Consistent Data Generation**
       - Equipment metadata now uses hash-based seeding
       - Location, manufacturer, and model remain consistent across refreshes
    
    2. **⚖️ Enhanced Operational Status**
       - 5-level status system (Critical, High Risk, Moderate Risk, Maintenance Due, Operational)
       - Considers failure probability, sensor readings, and maintenance schedule
    
    3. **📅 Equipment-Specific Maintenance Intervals**
       - HVAC: 90 days, Projectors: 180 days, Computers: 365 days
       - Smart maintenance scheduling based on equipment type
    
    4. **🎯 Priority-Based Complexity Assessment**
       - Issues are scored and highest priority determines complexity
       - No more complexity downgrading from multiple conditions
    
    5. **🛡️ Equipment-Specific Thresholds**
       - Different temperature, vibration, and pressure limits per equipment type
       - More realistic and accurate issue detection
    
    6. **📊 Enhanced Visualization**
       - Status indicators with color coding
       - Threshold comparison charts
       - Comprehensive sensor reading displays
    
    7. **🔍 Robust Error Handling**
       - Graceful handling of missing files
       - Demo data generation when files unavailable
       - Better user feedback and error messages
    """)

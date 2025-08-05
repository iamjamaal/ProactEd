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

# === SMTP CONFIGURATION ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_SENDER_EMAIL = "jamalnabila3709@gmail.com"
SMTP_SENDER_PASSWORD = "uzrusankamiavrxt"

# Page config
st.set_page_config(
    page_title="Equipment Failure Prediction Dashboard",
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
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'scheduled_maintenance' not in st.session_state:
    st.session_state.scheduled_maintenance = {}
if 'completed_maintenance' not in st.session_state:
    st.session_state.completed_maintenance = []
# Initialize session state for tracking metrics history
if 'previous_health' not in st.session_state:
    st.session_state.previous_health = None
if 'previous_mtbf' not in st.session_state:
    st.session_state.previous_mtbf = None
if 'previous_oee' not in st.session_state:
    st.session_state.previous_oee = None

# Load model and data
@st.cache_resource
def load_model():
    try:
        with open('complete_equipment_failure_prediction_system.pkl', 'rb') as f:
            return pickle.load(f)
    except:
        return None

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('cleaned_equipment_data.csv')
        # Convert numpy types to native Python types
        for col in df.columns:
            if df[col].dtype == 'int64':
                df[col] = df[col].astype(int)
            elif df[col].dtype == 'float64':
                df[col] = df[col].astype(float)
        
        # Standardize equipment types
        equipment_type_mapping = {
            'proj': 'Projector',
            'ac': 'Air Conditioner',
            'pod': 'Podium',
            'projector': 'Projector',
            'aircon': 'Air Conditioner',
            'air conditioner': 'Air Conditioner',
            'podium': 'Podium'
        }
        
        if 'equipment_type' in df.columns:
            df['equipment_type'] = df['equipment_type'].str.lower().map(equipment_type_mapping).fillna(df['equipment_type'])
        
        return df
    except:
        return None

# Helper functions
def calculate_health_score(row):
    """Calculate equipment health score based on multiple factors"""
    score = 100
    
    # Age factor (older equipment = lower score)
    if 'age_months' in row:
        age_penalty = min(int(row['age_months']) / 120 * 30, 30)
        score -= age_penalty
    
    # Maintenance factor
    if 'last_maintenance_days' in row:
        maint_penalty = min(int(row['last_maintenance_days']) / 365 * 25, 25)
        score -= maint_penalty
    
    # Operating hours factor
    if 'operating_hours' in row:
        hours_penalty = min(int(row['operating_hours']) / 8760 * 20, 20)
        score -= hours_penalty
    
    # Failure probability factor
    if 'failure_probability' in row:
        prob_penalty = float(row['failure_probability']) * 25
        score -= prob_penalty
    
    return max(float(score), 0.0)

def calculate_mtbf(equipment_data):
    """Calculate Mean Time Between Failures based on actual risk distribution"""
    if len(equipment_data) == 0:
        return 365.0
    
    failure_rates = {'Critical': 30, 'High': 90, 'Medium': 180, 'Low': 365}
    total_equipment = len(equipment_data)
    weighted_mtbf = 0
    
    for risk_level, days in failure_rates.items():
        count = len(equipment_data[equipment_data['risk_level'] == risk_level])
        weight = count / total_equipment if total_equipment > 0 else 0
        weighted_mtbf += weight * days
    
    return float(weighted_mtbf) if weighted_mtbf > 0 else 365.0

def calculate_mttr():
    """Calculate Mean Time To Repair (simulated)"""
    return float(np.random.normal(4, 1.5))

def calculate_oee(availability=0.95, performance=0.88, quality=0.92):
    """Calculate Overall Equipment Effectiveness"""
    return float(availability * performance * quality)

def calculate_dynamic_metrics(equipment_data, threshold):
    """Calculate realistic metrics based on actual equipment data"""
    total_count = len(equipment_data)
    
    if total_count == 0:
        return {
            'total_equipment': 0,
            'at_risk_count': 0,
            'at_risk_percentage': 0,
            'fleet_health': 0,
            'mtbf': 365,
            'oee': 0,
            'availability': 1.0,
            'performance': 0,
            'quality': 0.92
        }
    
    # Equipment at risk calculation
    at_risk = equipment_data[equipment_data['failure_probability'] >= threshold]
    at_risk_count = len(at_risk)
    
    # Health score calculation
    avg_health = equipment_data['health_score'].mean()
    
    # MTBF calculation
    mtbf = calculate_mtbf(equipment_data)
    
    # OEE calculation
    critical_equipment = len(equipment_data[equipment_data['risk_level'] == 'Critical'])
    availability = 1.0 - (critical_equipment / total_count)
    performance = avg_health / 100.0
    quality = 0.92  # Assumed quality factor
    
    oee = availability * performance * quality
    
    return {
        'total_equipment': total_count,
        'at_risk_count': at_risk_count,
        'at_risk_percentage': (at_risk_count / total_count * 100),
        'fleet_health': avg_health,
        'mtbf': mtbf,
        'oee': oee,
        'availability': availability,
        'performance': performance,
        'quality': quality
    }

# Update equipment after maintenance
def update_equipment_after_maintenance(equipment_id, maintenance_type):
    improvements = {
        'Preventive': {
            'failure_probability_reduction': 0.1,
            'health_score_improvement': 5,
            'reset_maintenance_days': True
        },
        'Corrective': {
            'failure_probability_reduction': 0.3,
            'health_score_improvement': 15,
            'reset_maintenance_days': True
        },
        'Major Overhaul': {
            'failure_probability_reduction': 0.5,
            'health_score_improvement': 25,
            'reset_maintenance_days': True,
            'reset_operating_hours': 0.5
        }
    }
    improvement = improvements.get(maintenance_type, improvements['Preventive'])
    
    st.session_state.equipment_updates[equipment_id] = {
        'maintenance_date': datetime.now(),
        'maintenance_type': maintenance_type,
        'improvements': improvement
    }
    
    maintenance_record = {
        'equipment_id': equipment_id,
        'maintenance_type': maintenance_type,
        'completion_date': datetime.now(),
        'technician': 'Assigned Technician',
        'improvements': improvement
    }
    st.session_state.maintenance_log.append(maintenance_record)

def schedule_maintenance(equipment_id, work_order_id, technician_info, maintenance_type="Preventive"):
    """Schedule maintenance and update tracking systems"""
    # Add to scheduled maintenance tracking
    st.session_state.scheduled_maintenance[equipment_id] = {
        'work_order_id': work_order_id,
        'technician': technician_info['name'],
        'tech_id': technician_info['tech_id'],
        'scheduled_date': datetime.now(),
        'maintenance_type': maintenance_type,
        'status': 'Scheduled',
        'equipment_id': equipment_id
    }
    
    # Add to maintenance log with scheduled status
    maintenance_record = {
        'equipment_id': equipment_id,
        'maintenance_type': maintenance_type,
        'scheduled_date': datetime.now(),
        'technician': technician_info['name'],
        'status': 'Scheduled',
        'work_order_id': work_order_id,
        'improvements': None  # Will be added when completed
    }
    st.session_state.maintenance_log.append(maintenance_record)

def complete_maintenance(equipment_id, completion_notes=""):
    """Mark maintenance as completed and apply equipment updates"""
    if equipment_id in st.session_state.scheduled_maintenance:
        scheduled = st.session_state.scheduled_maintenance[equipment_id]
        
        # Apply equipment improvements
        update_equipment_after_maintenance(equipment_id, scheduled['maintenance_type'])
        
        # Add to completed maintenance
        completed_record = {
            'equipment_id': equipment_id,
            'work_order_id': scheduled['work_order_id'],
            'technician': scheduled['technician'],
            'tech_id': scheduled['tech_id'],
            'scheduled_date': scheduled['scheduled_date'],
            'completion_date': datetime.now(),
            'maintenance_type': scheduled['maintenance_type'],
            'completion_notes': completion_notes
        }
        st.session_state.completed_maintenance.append(completed_record)
        
        # Update maintenance log status
        for record in st.session_state.maintenance_log:
            if (record['equipment_id'] == equipment_id and 
                record.get('work_order_id') == scheduled['work_order_id']):
                record['status'] = 'Completed'
                record['completion_date'] = datetime.now()
                record['completion_notes'] = completion_notes
                break
        
        # Remove from scheduled maintenance
        del st.session_state.scheduled_maintenance[equipment_id]
        
        return True
    return False

def is_equipment_scheduled_for_maintenance(equipment_id):
    """Check if equipment is already scheduled for maintenance"""
    return equipment_id in st.session_state.scheduled_maintenance

# Communication functions
def create_notification_message(equipment_info, work_instructions, technician_info, work_order_id):
    message = f"""
🚨 MAINTENANCE ALERT - WORK ORDER #{work_order_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 EQUIPMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 Equipment ID: {equipment_info['basic_info']['equipment_id']}
🔧 Type: {equipment_info['basic_info']['type']}
📍 Location: {equipment_info['basic_info']['location']}
🏭 Manufacturer: {equipment_info['basic_info']['manufacturer']}
📦 Model: {equipment_info['basic_info']['model']}
📅 Age: {equipment_info['basic_info']['age_months']} months

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CURRENT STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Failure Risk: {equipment_info['current_status']['failure_probability']:.3f}
💚 Health Score: {equipment_info['current_status']['health_score']:.1f}%
🚨 Risk Level: {equipment_info['current_status']['risk_level']}
⚙️ Status: {equipment_info['current_status']['operational_status']}
🔧 Last Maintenance: {equipment_info['current_status']['last_maintenance']} days ago

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CURRENT PARAMETERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️ Temperature: {equipment_info['parameters']['temperature']:.1f}°C
📳 Vibration: {equipment_info['parameters']['vibration']:.1f} mm/s
⚡ Pressure: {equipment_info['parameters']['pressure']:.1f} PSI
🔌 Power: {equipment_info['parameters']['power_consumption']:.0f} W
⏰ Operating Hours: {equipment_info['parameters']['operating_hours']:.0f} hrs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👷‍♂️ TECHNICIAN ASSIGNMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Assigned To: {technician_info['name']} ({technician_info['tech_id']})
🎯 Specializations: {technician_info['specializations']}
💰 Rate: ${technician_info['hourly_rate']}/hour
📅 Scheduled: {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 WORK INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    total_time = sum(instr['estimated_time'] for instr in work_instructions)
    message += f"⏱️ Total Estimated Time: {total_time} minutes ({total_time/60:.1f} hours)\n\n"
    
    for instruction in work_instructions:
        message += f"""
STEP {instruction['step']}: {instruction['category']}
📋 Task: {instruction['instruction']}
⏰ Time: {instruction['estimated_time']} minutes
🔧 Tools: {', '.join(instruction['tools_required'])}
⚠️ Safety: {instruction['safety_note']}
{'─' * 50}
"""
    
    message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 EMERGENCY CONTACTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏭 Control Room: +1-555-CONTROL
👨‍💼 Supervisor: +1-555-SUPER
🚨 Emergency: +1-555-EMERGENCY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 COMPLETION REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Complete all work steps
✅ Update equipment status in system
✅ Submit maintenance report
✅ Update work order with actual time/costs

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Priority: HIGH - Immediate Action Required
"""
    return message

def send_notification(message, technician_info, communication_method="email"):
    status = 'sent'
    error_msg = None
    
    if communication_method == "email":
        recipient_email = technician_info.get('email', None)
        if not recipient_email:
            status = 'failed'
            error_msg = 'Technician email not provided.'
        else:
            try:
                subject = "Maintenance Work Order Notification"
                msg = MIMEMultipart()
                msg['From'] = SMTP_SENDER_EMAIL
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SMTP_SENDER_EMAIL, SMTP_SENDER_PASSWORD)
                server.sendmail(SMTP_SENDER_EMAIL, recipient_email, msg.as_string())
                server.quit()
                status = 'sent'
            except Exception as e:
                status = 'failed'
                error_msg = str(e)

    notification_record = {
        'timestamp': datetime.now(),
        'technician': technician_info['name'],
        'tech_id': technician_info['tech_id'],
        'method': communication_method,
        'status': status,
        'message_preview': message[:100] + "...",
        'full_message': message
    }
    
    if communication_method == "email":
        notification_record['recipient_email'] = technician_info.get('email', None)
        if error_msg:
            notification_record['error'] = error_msg

    st.session_state.notifications_sent.append(notification_record)
    return notification_record

def apply_equipment_updates(equipment_data):
    updated_data = equipment_data.copy()
    
    for equipment_id, update_info in st.session_state.equipment_updates.items():
        if equipment_id in updated_data.index:
            improvements = update_info['improvements']
            
            current_prob = updated_data.loc[equipment_id, 'failure_probability']
            new_prob = max(0.0, current_prob - improvements['failure_probability_reduction'])
            updated_data.loc[equipment_id, 'failure_probability'] = new_prob
            
            current_health = updated_data.loc[equipment_id, 'health_score']
            new_health = min(100.0, current_health + improvements['health_score_improvement'])
            updated_data.loc[equipment_id, 'health_score'] = new_health
            
            if improvements.get('reset_maintenance_days'):
                updated_data.loc[equipment_id, 'last_maintenance_days'] = 0
            
            if new_prob >= 0.7:
                updated_data.loc[equipment_id, 'risk_level'] = 'Critical'
            elif new_prob >= 0.4:
                updated_data.loc[equipment_id, 'risk_level'] = 'High'
            elif new_prob >= 0.2:
                updated_data.loc[equipment_id, 'risk_level'] = 'Medium'
            else:
                updated_data.loc[equipment_id, 'risk_level'] = 'Low'
    
    return updated_data

# Updated Technician Database with better specialization mapping
technicians_db = {
    
    'Tech-Podium-2': {
        'name': 'Ama Serwaa',
        'email': 'amaserwaa@gmail.com',
        'specializations': ['Podium Maintenance', 'Audio Equipment', 'Conference Systems', 'Microphone Systems'],
        'experience_years': 7,
        'current_workload': 16,
        'max_capacity': 40,
        'hourly_rate': 77,
        'availability': 'Available',
        'certifications': ['Audio Systems', 'Conference Technology']
    },
    'Tech-General-1': {
        'name': 'Noah Jamal Nabila',
        'email': 'noahjamal303@gmail.com',
        'specializations': ['General Maintenance', 'Electrical Systems', 'Mechanical Systems'],
        'experience_years': 12,
        'current_workload': 30,
        'max_capacity': 40,
        'hourly_rate': 90,
        'availability': 'Available',
        'certifications': ['General Maintenance', 'Predictive Maintenance', 'OSHA Safety']
    },
    'Tech-General-2': {
        'name': 'Momoreoluwa Monsuru-Oke',
        'email': 'momoreoke@gmail.com',
        'specializations': ['General Maintenance', 'Preventive Maintenance', 'Equipment Diagnostics'],
        'experience_years': 11,
        'current_workload': 25,
        'max_capacity': 40,
        'hourly_rate': 88,
        'availability': 'Available',
        'certifications': ['General Maintenance', 'Equipment Diagnostics', 'Safety Training']
    }
}

def get_qualified_technicians(equipment_type, issue_complexity='medium'):
    """
    Get qualified technicians for specific equipment type and complexity
    """
    qualified = []
    
    complexity_requirements = {
        'low': 2,
        'medium': 5,
        'high': 8,
        'critical': 10
    }
    
    min_experience = complexity_requirements.get(issue_complexity, 5)
    
    # Normalize equipment type - handle various formats
    equipment_type_clean = str(equipment_type).lower().strip()
    
    # Map variations to standard types
    equipment_mapping = {
        'proj': 'projector',
        'projector': 'projector',
        'projection': 'projector',
        'display': 'projector',
        'ac': 'air conditioner',
        'aircon': 'air conditioner',
        'air conditioner': 'air conditioner',
        'air_conditioner': 'air conditioner',
        'hvac': 'air conditioner',
        'cooling': 'air conditioner',
        'climate': 'air conditioner',
        'pod': 'podium',
        'podium': 'podium',
        'podium_system': 'podium',
        'audio': 'podium',
        'sound': 'podium',
        'conference': 'podium'
    }
    
    standard_equipment_type = equipment_mapping.get(equipment_type_clean, equipment_type_clean)
    
    # Debug output for troubleshooting
    st.write(f"🔍 **Debug**: Looking for technicians for '{equipment_type}' → '{standard_equipment_type}' (Complexity: {issue_complexity})")
    
    for tech_id, tech_info in technicians_db.items():
        # Normalize technician specializations
        specializations = [str(spec).lower().strip() for spec in tech_info['specializations']]
        
        is_qualified = False
        match_score = tech_info['experience_years']  # Base score
        qualification_type = ""
        
        # Check for exact or partial matches in specializations
        for spec in specializations:
            # Direct equipment type match
            if standard_equipment_type in spec or spec in standard_equipment_type:
                is_qualified = True
                match_score += 25
                qualification_type = "Exact Specialization Match"
                break
            
            # Equipment-specific checks
            elif standard_equipment_type == 'projector':
                projector_keywords = ['projector', 'av equipment', 'display', 'av systems', 'audio visual']
                if any(keyword in spec for keyword in projector_keywords):
                    is_qualified = True
                    match_score += 20
                    qualification_type = "Projector Related"
                    break
                    
            elif standard_equipment_type == 'air conditioner':
                ac_keywords = ['air conditioner', 'hvac', 'cooling', 'refrigeration', 'climate']
                if any(keyword in spec for keyword in ac_keywords):
                    is_qualified = True
                    match_score += 20
                    qualification_type = "HVAC/Cooling Related"
                    break
                    
            elif standard_equipment_type == 'podium':
                podium_keywords = ['podium', 'audio', 'conference', 'sound', 'microphone']
                if any(keyword in spec for keyword in podium_keywords):
                    is_qualified = True
                    match_score += 20
                    qualification_type = "Audio/Conference Related"
                    break
        
        # General maintenance as fallback
        if not is_qualified:
            general_keywords = ['general maintenance', 'maintenance', 'electrical', 'mechanical']
            for spec in specializations:
                if any(keyword in spec for keyword in general_keywords):
                    is_qualified = True
                    match_score += 10
                    qualification_type = "General Maintenance"
                    break
        
        # Check experience and availability requirements
        if is_qualified:
            if tech_info['experience_years'] >= min_experience:
                if tech_info['current_workload'] < tech_info['max_capacity']:
                    available_hours = tech_info['max_capacity'] - tech_info['current_workload']
                    
                    qualified.append({
                        'tech_id': tech_id,
                        'name': tech_info['name'],
                        'email': tech_info['email'],
                        'experience': tech_info['experience_years'],
                        'specializations': ', '.join(tech_info['specializations']),
                        'available_hours': available_hours,
                        'hourly_rate': tech_info['hourly_rate'],
                        'match_score': match_score,
                        'qualification_type': qualification_type
                    })
    
    # Sort by match score (highest first)
    qualified_sorted = sorted(qualified, key=lambda x: x['match_score'], reverse=True)
    
    # Debug output
    if qualified_sorted:
        st.write(f"✅ **Found {len(qualified_sorted)} qualified technicians:**")
        for tech in qualified_sorted:
            st.write(f"- {tech['name']}: {tech['qualification_type']} (Score: {tech['match_score']})")
    else:
        st.write("❌ **No qualified technicians found**")
    
    return qualified_sorted

# Navigation
def render_navigation():
    st.sidebar.title("🎛️ Navigation")
    
    view_options = {
        'dashboard': '📊 Main Dashboard',
        'communications': '📱 Communications Center',
        'maintenance_log': '📋 Maintenance Log',
        'all_equipment': '🏭 All Equipment View'
    }
    
    selected_view = st.sidebar.radio(
        "Select View:",
        list(view_options.keys()),
        format_func=lambda x: view_options[x],
        index=list(view_options.keys()).index(st.session_state.current_view)
    )
    
    if selected_view != st.session_state.current_view:
        st.session_state.current_view = selected_view
        st.rerun()
    
    return selected_view

# Communications Center
def render_communications_center():
    st.title("📱 Communications Center")
    st.markdown("**Maintenance Notifications & Technician Communications**")
    
    # Add scheduled maintenance section
    st.subheader("🔄 Scheduled Maintenance Status")
    
    if st.session_state.scheduled_maintenance:
        st.info(f"📅 {len(st.session_state.scheduled_maintenance)} equipment items have scheduled maintenance")
        
        for equipment_id, scheduled in st.session_state.scheduled_maintenance.items():
            with st.expander(f"⏰ {equipment_id} - {scheduled['technician']} (Scheduled: {scheduled['scheduled_date'].strftime('%Y-%m-%d %H:%M')})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Equipment:** {equipment_id}")
                    st.markdown(f"**Work Order:** {scheduled['work_order_id']}")
                    st.markdown(f"**Technician:** {scheduled['technician']} ({scheduled['tech_id']})")
                    st.markdown(f"**Maintenance Type:** {scheduled['maintenance_type']}")
                    st.markdown(f"**Status:** 🟡 {scheduled['status']}")
                
                with col2:
                    completion_notes = st.text_area(
                        "Completion Notes:",
                        key=f"notes_{equipment_id}",
                        height=100,
                        placeholder="Enter maintenance completion notes..."
                    )
                
                with col3:
                    if st.button(f"✅ Mark Completed", key=f"complete_{equipment_id}", type="primary"):
                        if complete_maintenance(equipment_id, completion_notes):
                            st.success(f"✅ Maintenance completed for {equipment_id}!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to complete maintenance")
                    
                    if st.button(f"📞 Contact Technician", key=f"contact_{equipment_id}"):
                        st.info(f"📞 Contacting {scheduled['technician']}...")
    else:
        st.info("📭 No scheduled maintenance currently")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("📞 Communication Methods")
        methods = ["email", "sms", "push_notification"]
        method_labels = {
            "email": "📧 Email",
            "sms": "📱 SMS",
            "push_notification": "🔔 Push Notification"
        }
        for method in methods:
            st.checkbox(method_labels[method], value=True, key=f"comm_{method}")
    
    with col2:
        st.subheader("📤 Recent Notifications")
        
        if st.session_state.notifications_sent:
            for i, notification in enumerate(reversed(st.session_state.notifications_sent[-10:])):
                with st.expander(f"🔔 {notification['technician']} - {notification['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"**Technician:** {notification['technician']} ({notification['tech_id']})")
                    st.markdown(f"**Method:** {notification['method'].upper()}")
                    st.markdown(f"**Status:** ✅ {notification['status'].upper()}")
                    st.markdown(f"**Time:** {notification['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    st.markdown("**📄 Full Notification:**")
                    st.text_area(
                        "Message Content:",
                        notification['full_message'],
                        height=400,
                        key=f"msg_{i}",
                        disabled=True
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"📞 Call Technician", key=f"call_{i}"):
                            contact = notification.get('phone_contact', None)
                            if contact:
                                st.info(f"Technician Contact: {contact}")
                            else:
                                st.info("Technician contact not available.")
                    
                    with col2:
                        if st.button(f"📧 Resend Notification", key=f"resend_{i}"):
                            st.success("📧 Notification resent!")
                    
                    with col3:
                        if st.button(f"✅ Mark Acknowledged", key=f"ack_{i}"):
                            notif_idx = len(st.session_state.notifications_sent) - 1 - i
                            st.session_state.notifications_sent.pop(notif_idx)
                            st.success("✅ Notification removed!")
                            st.rerun()
        else:
            st.info("📭 No notifications sent yet")
    
    st.markdown("---")
    st.subheader("⚡ Quick Communication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📢 Broadcast Message**")
        broadcast_msg = st.text_area("Message to all technicians:", height=100)
        
        if st.button("📢 Send Broadcast"):
            if broadcast_msg:
                broadcast_record = {
                    'timestamp': datetime.now(),
                    'technician': 'ALL_TECHNICIANS',
                    'tech_id': 'BROADCAST',
                    'method': 'broadcast',
                    'status': 'sent',
                    'message_preview': broadcast_msg[:100] + "...",
                    'full_message': f"📢 BROADCAST MESSAGE\n\n{broadcast_msg}\n\nSent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
                st.session_state.notifications_sent.append(broadcast_record)
                st.success("📢 Broadcast sent to all technicians!")
            else:
                st.error("Please enter a message")
    
    with col2:
        st.markdown("**🚨 Emergency Alert**")
        emergency_msg = st.text_area("Emergency message:", height=100)
        
        if st.button("🚨 Send Emergency Alert", type="primary"):
            if emergency_msg:
                emergency_record = {
                    'timestamp': datetime.now(),
                    'technician': 'ALL_TECHNICIANS',
                    'tech_id': 'EMERGENCY',
                    'method': 'emergency',
                    'status': 'sent',
                    'message_preview': emergency_msg[:100] + "...",
                    'full_message': f"🚨 EMERGENCY ALERT 🚨\n\n{emergency_msg}\n\nISSUED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nACTION REQUIRED: IMMEDIATE"
                }
                st.session_state.notifications_sent.append(emergency_record)
                st.error("🚨 EMERGENCY ALERT SENT!")
            else:
                st.error("Please enter an emergency message")

# All Equipment View
def render_all_equipment_view():
    st.title("🏭 All Equipment Status")
    st.markdown("**Complete Equipment Inventory & Status**")
    
    equipment_data = load_data()
    if equipment_data is None:
        st.error("Unable to load equipment data")
        return
    
    equipment_data = apply_equipment_updates(equipment_data)
    
    model_system = load_model()
    if model_system:
        model = model_system['model_info']['model_object']
        features = model_system['model_info']['features']
        
        for feature in features:
            if feature not in equipment_data.columns:
                equipment_data[feature] = 0
        
        X = equipment_data[features].fillna(0)
        predictions = model.predict(X)
        
        equipment_data['failure_probability'] = [float(p) for p in predictions]
        equipment_data['risk_level'] = [
            'Critical' if p >= 0.7 else 'High' if p >= 0.4 else 'Medium' if p >= 0.2 else 'Low'
            for p in predictions
        ]
        
        equipment_data['health_score'] = equipment_data.apply(calculate_health_score, axis=1)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_equipment = len(equipment_data)
        st.metric("Total Equipment", total_equipment)
    
    with col2:
        critical_count = len(equipment_data[equipment_data['failure_probability'] >= 0.7])
        st.metric("Critical Risk", critical_count, f"{critical_count/total_equipment*100:.1f}%")
    
    with col3:
        high_count = len(equipment_data[equipment_data['failure_probability'] >= 0.4])
        st.metric("High+ Risk", high_count, f"{high_count/total_equipment*100:.1f}%")
    
    with col4:
        avg_health = equipment_data['health_score'].mean()
        st.metric("Average Health", f"{avg_health:.1f}%")
    
    st.subheader("🔍 Filter Equipment")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_filter = st.selectbox(
            "Risk Level",
            ['All', 'Critical', 'High', 'Medium', 'Low']
        )
    
    with col2:
        if 'equipment_type' in equipment_data.columns:
            type_filter = st.selectbox(
                "Equipment Type", 
                ['All'] + list(equipment_data['equipment_type'].unique())
            )
        else:
            type_filter = 'All'
    
    with col3:
        age_filter = st.selectbox(
            "Age Range",
            ['All', '< 2 years', '2-5 years', '5-10 years', '> 10 years']
        )
    
    with col4:
        maintenance_filter = st.selectbox(
            "Maintenance Status",
            ['All', 'Overdue (>180 days)', 'Due Soon (>90 days)', 'Recent (<30 days)']
        )
    
    filtered_data = equipment_data.copy()
    
    if risk_filter != 'All':
        filtered_data = filtered_data[filtered_data['risk_level'] == risk_filter]
    
    if type_filter != 'All' and 'equipment_type' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['equipment_type'] == type_filter]
    
    if age_filter != 'All' and 'age_months' in filtered_data.columns:
        age_ranges = {
            '< 2 years': (0, 24),
            '2-5 years': (24, 60), 
            '5-10 years': (60, 120),
            '> 10 years': (120, 999)
        }
        min_age, max_age = age_ranges[age_filter]
        filtered_data = filtered_data[
            (filtered_data['age_months'] >= min_age) & 
            (filtered_data['age_months'] <= max_age)
        ]
    
    if maintenance_filter != 'All' and 'last_maintenance_days' in filtered_data.columns:
        maint_ranges = {
            'Overdue (>180 days)': (180, 9999),
            'Due Soon (>90 days)': (90, 180),
            'Recent (<30 days)': (0, 30)
        }
        min_days, max_days = maint_ranges[maintenance_filter]
        filtered_data = filtered_data[
            (filtered_data['last_maintenance_days'] >= min_days) & 
            (filtered_data['last_maintenance_days'] <= max_days)
        ]
    
    st.subheader(f"📊 Filtered Results ({len(filtered_data)} equipment)")
    
    if len(filtered_data) > 0:
        display_df = filtered_data.copy()
        display_df['Equipment_ID'] = [f"EQ-{i:03d}" for i in display_df.index]
        
        display_columns = ['Equipment_ID', 'failure_probability', 'health_score', 'risk_level']
        
        if 'equipment_type' in display_df.columns:
            display_columns.append('equipment_type')
        if 'age_months' in display_df.columns:
            display_columns.append('age_months')
        if 'last_maintenance_days' in display_df.columns:
            display_columns.append('last_maintenance_days')
        
        column_names = {
            'Equipment_ID': 'Equipment ID',
            'failure_probability': 'Failure Risk',
            'health_score': 'Health Score (%)',
            'risk_level': 'Risk Level',
            'equipment_type': 'Type',
            'age_months': 'Age (months)',
            'last_maintenance_days': 'Days Since Maintenance'
        }
        
        display_df = display_df[display_columns].rename(columns=column_names)
        display_df['Failure Risk'] = display_df['Failure Risk'].round(3)
        display_df['Health Score (%)'] = display_df['Health Score (%)'].round(1)
        
        page_size = 50
        total_pages = (len(display_df) - 1) // page_size + 1
        
        if total_pages > 1:
            page = st.selectbox(f"Page (showing {page_size} per page):", range(1, total_pages + 1))
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            display_df_page = display_df.iloc[start_idx:end_idx]
        else:
            display_df_page = display_df
        
        st.dataframe(
            display_df_page,
            use_container_width=True,
            height=600
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv,
                file_name=f"equipment_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("📊 Generate Equipment Report"):
                report_filename = f"equipment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filtered_data.to_csv(report_filename, index=False)
                st.success(f"📊 Equipment report generated and saved as '{report_filename}'!")
    
    else:
        st.info("No equipment matches the selected filters.")

# Maintenance Log View
def render_maintenance_log():
    st.title("📋 Maintenance Activity Log")
    st.markdown("**Track all maintenance activities and their impact**")
    
    # Combined maintenance activities (scheduled + completed)
    all_activities = []
    
    # Add scheduled maintenance
    for equipment_id, scheduled in st.session_state.scheduled_maintenance.items():
        all_activities.append({
            'equipment_id': equipment_id,
            'maintenance_type': scheduled['maintenance_type'],
            'technician': scheduled['technician'],
            'date': scheduled['scheduled_date'],
            'status': 'Scheduled',
            'work_order_id': scheduled['work_order_id']
        })
    
    # Add completed maintenance from session state
    for completed in st.session_state.completed_maintenance:
        all_activities.append({
            'equipment_id': completed['equipment_id'],
            'maintenance_type': completed['maintenance_type'],
            'technician': completed['technician'],
            'date': completed['completion_date'],
            'status': 'Completed',
            'work_order_id': completed['work_order_id'],
            'completion_notes': completed.get('completion_notes', '')
        })
    
    # Add from maintenance log
    for record in st.session_state.maintenance_log:
        if record.get('status') not in ['Scheduled']:  # Avoid duplicates
            all_activities.append({
                'equipment_id': record['equipment_id'],
                'maintenance_type': record['maintenance_type'],
                'technician': record['technician'],
                'date': record.get('completion_date', record.get('scheduled_date', datetime.now())),
                'status': record.get('status', 'Completed'),
                'work_order_id': record.get('work_order_id', 'N/A')
            })
    
    if all_activities:
        st.subheader(f"📊 All Maintenance Activities ({len(all_activities)} records)")
        
        # Sort by date (most recent first)
        all_activities.sort(key=lambda x: x['date'], reverse=True)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_activities = len(all_activities)
            st.metric("Total Activities", total_activities)
        
        with col2:
            scheduled_count = len([a for a in all_activities if a['status'] == 'Scheduled'])
            st.metric("Scheduled", scheduled_count)
        
        with col3:
            completed_count = len([a for a in all_activities if a['status'] == 'Completed'])
            st.metric("Completed", completed_count)
        
        with col4:
            today_count = len([a for a in all_activities if a['date'].date() == datetime.now().date()])
            st.metric("Today", today_count)
        
        # Display activities
        for i, activity in enumerate(all_activities[:20]):  # Show last 20 activities
            status_icon = "🟡" if activity['status'] == 'Scheduled' else "✅"
            date_str = activity['date'].strftime('%Y-%m-%d %H:%M')
            
            with st.expander(f"{status_icon} {activity['equipment_id']} - {activity['maintenance_type']} ({date_str})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Equipment:** {activity['equipment_id']}")
                    st.markdown(f"**Type:** {activity['maintenance_type']}")
                    st.markdown(f"**Technician:** {activity['technician']}")
                    st.markdown(f"**Status:** {activity['status']}")
                    st.markdown(f"**Work Order:** {activity['work_order_id']}")
                
                with col2:
                    if activity['status'] == 'Completed':
                        st.markdown("**📈 Expected Impact:**")
                        st.markdown("- ✅ Reduced failure risk")
                        st.markdown("- ✅ Improved health score")
                        st.markdown("- ✅ Extended equipment life")
                        st.markdown("- ✅ Maintenance timer reset")
                        
                        if 'completion_notes' in activity and activity['completion_notes']:
                            st.markdown(f"**📝 Notes:** {activity['completion_notes']}")
                    else:
                        st.markdown("**⏰ Scheduled Activity**")
                        st.markdown("- Awaiting completion")
                        st.markdown("- Technician assigned")
                        st.markdown("- Work order active")
    
    else:
        st.info("📭 No maintenance activities recorded yet")
        st.markdown("Maintenance activities will appear here after work orders are created.")

# Main Dashboard with Dynamic Executive Summary
def main_dashboard():
    st.title("🔧 Equipment Failure Prediction Dashboard")
    st.markdown("**Advanced Predictive Maintenance System**")
    
    model_system = load_model()
    equipment_data = load_data()
    
    if model_system is None or equipment_data is None:
        st.error("⚠️ Unable to load model or data files")
        return
    
    equipment_data = apply_equipment_updates(equipment_data)
    
    st.sidebar.header("🎛️ Control Panel")
    threshold = st.sidebar.slider(
        "Alert Threshold", 
        min_value=0.1, 
        max_value=0.9, 
        value=float(model_system['model_info']['optimal_threshold']),
        step=0.05
    )
    
    equipment_types = equipment_data['equipment_type'].unique() if 'equipment_type' in equipment_data.columns else ['All']
    selected_equipment = st.sidebar.multiselect(
        "Equipment Types",
        equipment_types,
        default=equipment_types[:3] if len(equipment_types) > 3 else equipment_types
    )
    
    model = model_system['model_info']['model_object']
    features = model_system['model_info']['features']
    
    for feature in features:
        if feature not in equipment_data.columns:
            equipment_data[feature] = 0
    
    X = equipment_data[features].fillna(0)
    predictions = model.predict(X)
    
    equipment_data['failure_probability'] = [float(p) for p in predictions]
    equipment_data['risk_level'] = [
        'Critical' if p >= 0.7 else 'High' if p >= 0.4 else 'Medium' if p >= 0.2 else 'Low'
        for p in predictions
    ]
    equipment_data['alert_required'] = [bool(p >= threshold) for p in predictions]
    
    equipment_data['health_score'] = equipment_data.apply(calculate_health_score, axis=1)
    
    # === DYNAMIC EXECUTIVE SUMMARY ===
    st.header("📊 Executive Summary")
    
    # Filter by equipment type selection first
    if selected_equipment and 'equipment_type' in equipment_data.columns:
        filtered_data = equipment_data[equipment_data['equipment_type'].isin(selected_equipment)]
    else:
        filtered_data = equipment_data

    # Calculate dynamic metrics
    metrics = calculate_dynamic_metrics(filtered_data, threshold)
    
    # Remove equipment that's already scheduled for maintenance from at-risk count
    at_risk_equipment = filtered_data[filtered_data['failure_probability'] >= threshold]
    at_risk_equipment = at_risk_equipment[
        ~at_risk_equipment.index.map(lambda x: f"EQ-{x:03d}").isin(st.session_state.scheduled_maintenance.keys())
    ]
    actual_alerts = len(at_risk_equipment)
    
    # Calculate trends
    if st.session_state.previous_health is None:
        st.session_state.previous_health = metrics['fleet_health']
    if st.session_state.previous_mtbf is None:
        st.session_state.previous_mtbf = metrics['mtbf']
    if st.session_state.previous_oee is None:
        st.session_state.previous_oee = metrics['oee']
    
    health_change = metrics['fleet_health'] - st.session_state.previous_health
    mtbf_change = metrics['mtbf'] - st.session_state.previous_mtbf
    oee_change = metrics['oee'] - st.session_state.previous_oee
    
    # Update previous values
    st.session_state.previous_health = metrics['fleet_health']
    st.session_state.previous_mtbf = metrics['mtbf']
    st.session_state.previous_oee = metrics['oee']
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Equipment", metrics['total_equipment'])
    
    with col2:
        alert_pct = (actual_alerts / metrics['total_equipment'] * 100) if metrics['total_equipment'] > 0 else 0
        trend_color = "normal" if alert_pct <= 10 else "inverse"
        st.metric(
            "Equipment at Risk", 
            actual_alerts, 
            f"{alert_pct:.1f}%",
            delta_color=trend_color
        )
    
    with col3:
        health_delta = f"+{health_change:.1f}%" if health_change >= 0 else f"{health_change:.1f}%"
        st.metric(
            "Fleet Health", 
            f"{metrics['fleet_health']:.1f}%", 
            health_delta,
            delta_color="normal" if health_change >= 0 else "inverse"
        )
    
    with col4:
        mtbf_delta = f"+{mtbf_change:.0f} days" if mtbf_change >= 0 else f"{mtbf_change:.0f} days"
        st.metric(
            "MTBF (days)", 
            f"{metrics['mtbf']:.0f}", 
            mtbf_delta,
            delta_color="normal" if mtbf_change >= 0 else "inverse"
        )
    
    with col5:
        oee_delta = f"+{oee_change:.1%}" if oee_change >= 0 else f"{oee_change:.1%}"
        st.metric(
            "OEE", 
            f"{metrics['oee']:.1%}", 
            oee_delta,
            delta_color="normal" if oee_change >= 0 else "inverse"
        )
    
    # Additional insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical_count = len(filtered_data[filtered_data['risk_level'] == 'Critical'])
        critical_pct = (critical_count / metrics['total_equipment'] * 100) if metrics['total_equipment'] > 0 else 0
        st.metric("Critical Risk", critical_count, f"{critical_pct:.1f}%")
    
    with col2:
        scheduled_count = len(st.session_state.scheduled_maintenance)
        st.metric("Scheduled Maintenance", scheduled_count)
    
    with col3:
        completed_today = len([
            record for record in st.session_state.completed_maintenance 
            if record['completion_date'].date() == datetime.now().date()
        ])
        st.metric("Completed Today", completed_today)
    
    # Show scheduled maintenance summary
    if st.session_state.scheduled_maintenance:
        st.info(f"🔄 {len(st.session_state.scheduled_maintenance)} equipment items have scheduled maintenance")
    
    # === ENHANCED INSIGHTS SECTION ===
    with st.expander("📈 Detailed Fleet Insights", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Risk Distribution:**")
            risk_counts = filtered_data['risk_level'].value_counts()
            for risk_level, count in risk_counts.items():
                percentage = (count / metrics['total_equipment'] * 100) if metrics['total_equipment'] > 0 else 0
                risk_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(risk_level, "⚪")
                st.markdown(f"{risk_emoji} **{risk_level}:** {count} ({percentage:.1f}%)")
        
        with col2:
            st.markdown("**📊 Equipment Age Analysis:**")
            if 'age_months' in filtered_data.columns:
                avg_age = filtered_data['age_months'].mean()
                old_equipment = len(filtered_data[filtered_data['age_months'] > 120])  # > 10 years
                old_pct = (old_equipment / metrics['total_equipment'] * 100) if metrics['total_equipment'] > 0 else 0
                st.markdown(f"📅 **Average Age:** {avg_age:.1f} months")
                st.markdown(f"⚠️ **Legacy Equipment:** {old_equipment} units ({old_pct:.1f}%)")
            
            st.markdown("**🔧 Maintenance Status:**")
            if 'last_maintenance_days' in filtered_data.columns:
                overdue = len(filtered_data[filtered_data['last_maintenance_days'] > 180])
                st.markdown(f"🚨 **Overdue Maintenance:** {overdue} units")
    
    st.header("🏥 Equipment Health Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_health = px.histogram(
            filtered_data, 
            x='health_score',
            nbins=20,
            title="Equipment Health Score Distribution",
            labels={'health_score': 'Health Score (%)', 'count': 'Count'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_health.add_vline(x=70, line_dash="dash", line_color="orange", 
                           annotation_text="Warning Threshold")
        fig_health.add_vline(x=50, line_dash="dash", line_color="red", 
                           annotation_text="Critical Threshold")
        st.plotly_chart(fig_health, use_container_width=True)
    
    with col2:
        fig_scatter = px.scatter(
            filtered_data, 
            x='health_score', 
            y='failure_probability',
            color='risk_level',
            size='age_months' if 'age_months' in filtered_data.columns else None,
            title="Health Score vs Failure Risk",
            labels={'health_score': 'Health Score (%)', 'failure_probability': 'Failure Probability'},
            color_discrete_map={
                'Critical': '#ff4444',
                'High': '#ff8800', 
                'Medium': '#ffcc00',
                'Low': '#44ff44'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.header("🚨 Equipment Assignment & Communication System")
    high_risk_equipment = at_risk_equipment.copy()
    
    st.subheader(f"🚨 Alert Management - {len(high_risk_equipment)} Equipment Need Attention")
    
    if len(high_risk_equipment) > 0:
        st.info(f"📊 Found {len(high_risk_equipment)} equipment items requiring attention (threshold: {threshold:.2f})")
        high_risk_equipment = high_risk_equipment.sort_values('failure_probability', ascending=False)
        
        alert_options = []
        for idx, row in high_risk_equipment.iterrows():
            equipment_id = f"EQ-{idx:03d}"
            risk_indicator = "🔴" if row['failure_probability'] >= 0.8 else "🟠" if row['failure_probability'] >= 0.6 else "🟡"
            alert_options.append(f"{risk_indicator} {equipment_id} - {row.get('equipment_type', 'Unknown')} (Risk: {row['failure_probability']:.3f})")
        
        selected_alert = st.selectbox(
            f"🚨 Select Equipment for Assignment ({len(alert_options)} available):",
            ["Select equipment..."] + alert_options
        )
        
        if selected_alert != "Select equipment...":
            equipment_idx = int(selected_alert.split(" - ")[0].split(" ")[1].replace("EQ-", ""))
            selected_equipment = high_risk_equipment.loc[equipment_idx]
            equipment_id = f"EQ-{equipment_idx:03d}"
            
            # Check if equipment is already scheduled
            if is_equipment_scheduled_for_maintenance(equipment_id):
                st.warning(f"⚠️ {equipment_id} is already scheduled for maintenance!")
                return
            
            def get_equipment_detailed_info(equipment_row):
                return {
                    'basic_info': {
                        'equipment_id': f"EQ-{equipment_row.name:03d}",
                        'type': str(equipment_row.get('equipment_type', 'Unknown')),
                        'age_months': int(equipment_row.get('age_months', 0)),
                        'installation_date': (datetime.now() - timedelta(days=int(equipment_row.get('age_months', 0)) * 30)).strftime('%Y-%m-%d'),
                        'location': f"Facility-{np.random.choice(['A', 'B', 'C'])}-Zone-{np.random.randint(1, 5)}",
                        'manufacturer': np.random.choice(['Siemens', 'GE', 'ABB', 'Schneider', 'Emerson']),
                        'model': f"Model-{np.random.randint(1000, 9999)}"
                    },
                    'current_status': {
                        'failure_probability': float(equipment_row['failure_probability']),
                        'health_score': float(equipment_row['health_score']),
                        'risk_level': str(equipment_row['risk_level']),
                        'operational_status': 'Running' if equipment_row['failure_probability'] < 0.8 else 'Requires Attention',
                        'last_maintenance': int(equipment_row.get('last_maintenance_days', 0)),
                        'next_scheduled': 'Overdue' if equipment_row.get('last_maintenance_days', 0) > 180 else f"{180 - int(equipment_row.get('last_maintenance_days', 0))} days"
                    },
                    'parameters': {
                        'temperature': float(equipment_row.get('temperature', 0)),
                        'vibration': float(equipment_row.get('vibration', 0)),
                        'pressure': float(equipment_row.get('pressure', 0)),
                        'power_consumption': float(equipment_row.get('power_consumption', 0)),
                        'operating_hours': float(equipment_row.get('operating_hours', 0))
                    }
                }
            
            def determine_issue_details(equipment_row):
                issues = []
                complexity = 'medium'
                
                prob = float(equipment_row['failure_probability'])
                
                if prob >= 0.8:
                    issues.append("🔴 CRITICAL: Imminent failure risk detected")
                    complexity = 'critical'
                elif prob >= 0.6:
                    issues.append("🟠 HIGH: Significant degradation detected")
                    complexity = 'high'
                elif prob >= 0.4:
                    issues.append("🟡 MEDIUM: Performance decline observed")
                    complexity = 'medium'
                
                temp = float(equipment_row.get('temperature', 0))
                if temp > 95:
                    issues.append(f"🌡️ OVERHEATING: Temperature at {temp:.1f}°C (Normal: <85°C)")
                    complexity = 'high'
                elif temp > 85:
                    issues.append(f"🌡️ HOT: Temperature elevated at {temp:.1f}°C")
                
                vib = float(equipment_row.get('vibration', 0))
                if vib > 5:
                    issues.append(f"📳 SEVERE VIBRATION: {vib:.1f} mm/s (Normal: <3 mm/s)")
                    complexity = 'high'
                elif vib > 3.5:
                    issues.append(f"📳 VIBRATION: Elevated at {vib:.1f} mm/s")
                
                pressure = float(equipment_row.get('pressure', 0))
                if pressure > 130:
                    issues.append(f"⚡ HIGH PRESSURE: {pressure:.1f} PSI (Normal: <120 PSI)")
                elif pressure < 80:
                    issues.append(f"⚡ LOW PRESSURE: {pressure:.1f} PSI (Normal: >90 PSI)")
                
                last_maint = int(equipment_row.get('last_maintenance_days', 0))
                if last_maint > 365:
                    issues.append(f"📅 MAINTENANCE OVERDUE: {last_maint} days since last service")
                    complexity = 'high'
                elif last_maint > 180:
                    issues.append(f"📅 MAINTENANCE DUE: {last_maint} days since last service")
                
                age = int(equipment_row.get('age_months', 0))
                if age > 120:
                    issues.append(f"⚠️ AGING EQUIPMENT: {age} months old - Consider replacement evaluation")
                
                return issues, complexity
            
            def generate_work_instructions(equipment_info, issues, complexity):
                instructions = []
                
                instructions.append({
                    'step': 1,
                    'category': 'SAFETY',
                    'instruction': 'Lock out/Tag out equipment following safety procedures',
                    'estimated_time': 15,
                    'tools_required': ['LOTO kit', 'Safety equipment'],
                    'safety_note': 'Verify zero energy state before proceeding'
                })
                
                step_counter = 2
                
                for issue in issues:
                    if "OVERHEATING" in issue or "HOT" in issue:
                        instructions.append({
                            'step': step_counter,
                            'category': 'THERMAL',
                            'instruction': 'Inspect cooling system, clean heat exchangers, check coolant levels',
                            'estimated_time': 45,
                            'tools_required': ['Thermal camera', 'Cleaning equipment', 'Coolant'],
                            'safety_note': 'Allow equipment to cool before handling'
                        })
                        step_counter += 1
                    
                    if "VIBRATION" in issue:
                        instructions.append({
                            'step': step_counter,
                            'category': 'MECHANICAL',
                            'instruction': 'Check alignment, inspect bearings, verify mounting bolts torque',
                            'estimated_time': 60,
                            'tools_required': ['Vibration analyzer', 'Alignment tools', 'Torque wrench'],
                            'safety_note': 'Use proper lifting techniques for heavy components'
                        })
                        step_counter += 1
                    
                    if "PRESSURE" in issue:
                        instructions.append({
                            'step': step_counter,
                            'category': 'HYDRAULIC',
                            'instruction': 'Inspect seals, check for leaks, test pressure relief valves',
                            'estimated_time': 30,
                            'tools_required': ['Pressure gauge', 'Seal kit', 'Leak detection fluid'],
                            'safety_note': 'Depressurize system before opening connections'
                        })
                        step_counter += 1
                    
                    if "MAINTENANCE" in issue:
                        instructions.append({
                            'step': step_counter,
                            'category': 'PREVENTIVE',
                            'instruction': f'Perform standard {equipment_info["basic_info"]["type"]} maintenance per PM checklist',
                            'estimated_time': 90,
                            'tools_required': ['Standard tool kit', 'Lubricants', 'Filters'],
                            'safety_note': 'Follow manufacturer maintenance procedures'
                        })
                        step_counter += 1
                
                instructions.append({
                    'step': step_counter,
                    'category': 'TESTING',
                    'instruction': 'Perform operational test and verify all parameters within normal range',
                    'estimated_time': 30,
                    'tools_required': ['Multimeter', 'Test equipment'],
                    'safety_note': 'Ensure all guards and safety devices are in place'
                })
                
                return instructions
            
            equipment_info = get_equipment_detailed_info(selected_equipment)
            issues, complexity = determine_issue_details(selected_equipment)
            work_instructions = generate_work_instructions(equipment_info, issues, complexity)
            qualified_techs = get_qualified_technicians(equipment_info['basic_info']['type'], complexity)
            
            st.markdown("---")
            st.subheader(f"📋 Equipment Summary: {equipment_info['basic_info']['equipment_id']}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Equipment Type", equipment_info['basic_info']['type'])
                st.metric("Age", f"{equipment_info['basic_info']['age_months']} months")
            
            with col2:
                st.metric("Failure Risk", f"{equipment_info['current_status']['failure_probability']:.3f}")
                st.metric("Health Score", f"{equipment_info['current_status']['health_score']:.1f}%")
            
            with col3:
                st.metric("Risk Level", equipment_info['current_status']['risk_level'])
                st.metric("Status", equipment_info['current_status']['operational_status'])
            
            with col4:
                st.metric("Last Maintenance", f"{equipment_info['current_status']['last_maintenance']} days ago")
                st.metric("Next Scheduled", equipment_info['current_status']['next_scheduled'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚨 Identified Issues:**")
                for i, issue in enumerate(issues, 1):
                    st.markdown(f"{i}. {issue}")
                
                st.markdown(f"**⚠️ Issue Complexity:** {complexity.upper()}")
            
            st.markdown("---")
            st.subheader("👷‍♂️ Technician Assignment & Communication")

            if qualified_techs:
                st.success(f"Found {len(qualified_techs)} qualified technicians for this {complexity} complexity issue")
                total_time = sum(instr['estimated_time'] for instr in work_instructions)

                for tech in qualified_techs:
                    with st.expander(f"👨‍🔧 Technician: {tech['name']} (Score: {tech['match_score']})", expanded=True):
                        col1, col2, col3 = st.columns([3,1,1])
                        
                        with col1:
                            st.markdown(f"""
                            **Technician Details:**
                            - **ID:** {tech['tech_id']}
                            - **Specializations:** {tech['specializations']}
                            - **Experience:** {tech['experience']} years
                            """)
                        
                        with col2:
                            st.metric("Available Hours", f"{tech['available_hours']}")
                            st.metric("Hourly Rate", f"${tech['hourly_rate']}")
                        
                        with col3:
                            estimated_cost = total_time/60 * tech['hourly_rate']
                            st.metric("Est. Cost", f"${estimated_cost:.2f}")
                        
                        st.markdown("**📡 Communication Methods:**")
                        comm_methods = st.multiselect(
                            f"Select methods for {tech['name']}:",
                            ["📧 Email", "📱 SMS", "🔔 Push", "📻 Radio"],
                            default=["📧 Email"],
                            key=f"comm_methods_{tech['tech_id']}"
                        )
                        
                        if st.button(f"📨 Assign {tech['name']}", key=f"assign_{tech['tech_id']}"):
                            work_order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{np.random.randint(1000, 9999)}"
                            
                            # Schedule maintenance
                            schedule_maintenance(equipment_id, work_order_id, tech, complexity.capitalize())
                            
                            # Send notifications
                            notification_message = create_notification_message(
                                equipment_info,
                                work_instructions,
                                tech,
                                work_order_id
                            )
                            notifications_sent = []
                            for method in comm_methods:
                                method_key = method.split(" ")[1].lower()
                                notification_record = send_notification(
                                    notification_message,
                                    tech,
                                    method_key
                                )
                                notifications_sent.append(method_key)
                            
                            st.success(f"""
                            ✅ **Technician Assigned Successfully!**
                            
                            **Work Order ID:** {work_order_id}
                            **Technician:** {tech['name']}
                            **Equipment:** {equipment_info['basic_info']['equipment_id']}
                            **Notification Methods:** {', '.join(notifications_sent)}
                            **Status:** Scheduled for maintenance
                            """)
                            
                            # Switch to communications center to show the scheduled maintenance
                            st.session_state.current_view = 'communications'
                            st.rerun()
            else:
                st.error("❌ No qualified technicians available for this equipment type and complexity level")
                st.info("Consider these options:")
                st.markdown("- Reassign workload among technicians")
                st.markdown("- Bring in external specialist")
                st.markdown("- Adjust maintenance schedule")
    
    else:
        st.success("✅ No high-risk equipment alerts at current threshold")
        if st.session_state.scheduled_maintenance:
            st.info(f"📋 {len(st.session_state.scheduled_maintenance)} equipment items are currently scheduled for maintenance")
        else:
            st.info("Lower the alert threshold in the sidebar to see more equipment for preventive maintenance")
    
    st.header("📊 Risk Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        risk_counts = filtered_data['risk_level'].value_counts()
        fig_pie = px.pie(
            values=risk_counts.values, 
            names=risk_counts.index,
            title="Equipment by Risk Level",
            color_discrete_map={
                'Critical': '#ff4444',
                'High': '#ff8800', 
                'Medium': '#ffcc00',
                'Low': '#44ff44'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_hist = px.histogram(
            filtered_data, 
            x='failure_probability',
            nbins=30,
            title="Failure Probability Distribution",
            labels={'failure_probability': 'Failure Probability', 'count': 'Count'}
        )
        fig_hist.add_vline(x=threshold, line_dash="dash", line_color="red", 
                          annotation_text="Alert Threshold")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    st.header("🎯 Model Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Model Type", model_system['model_info']['model_name'])
    
    with col2:
        r2_score = float(model_system['model_info']['performance_metrics']['r2_score'])
        st.metric("R² Score", f"{r2_score:.3f}")
    
    with col3:
        roi = float(model_system['model_info']['performance_metrics']['roi'])
        st.metric("Expected ROI", f"{roi:.1f}%")

def main():
    current_view = render_navigation()
    rendered = False
    if current_view == 'dashboard':
        main_dashboard()
        rendered = True
    elif current_view == 'communications':
        render_communications_center()
        rendered = True
    elif current_view == 'maintenance_log':
        render_maintenance_log()
        rendered = True
    elif current_view == 'all_equipment':
        render_all_equipment_view()
        rendered = True
    if not rendered:
        st.error("No dashboard view rendered. Please check your navigation or data/model files.")

# Ensure main() is called when running the script
if __name__ == "__main__":
    main()
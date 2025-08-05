# dashboard_integration.py
# Phase 2: Integration code for your existing predictive maintenance dashboard
# Add these functions to your main dashboard file

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import your new services (make sure these paths match your project structure)
try:
    from services.email_service import EmailService, NotificationManager
    from config.settings import Config
except ImportError:
    st.warning("Email services not available. Complete Phase 1 and 2 setup first.")

def initialize_notification_system():
    """Initialize the notification system - call this at the start of your dashboard"""
    
    if 'notification_manager' not in st.session_state:
        try:
            config = Config()
            
            if config.is_email_configured():
                email_service = EmailService(
                    smtp_server=config.SMTP_SERVER,
                    smtp_port=config.SMTP_PORT,
                    username=config.EMAIL_USERNAME,
                    password=config.EMAIL_PASSWORD
                )
                st.session_state.notification_manager = NotificationManager(email_service)
                st.session_state.email_configured = True
            else:
                st.session_state.notification_manager = None
                st.session_state.email_configured = False
                
        except Exception as e:
            st.session_state.notification_manager = None
            st.session_state.email_configured = False
            if st.sidebar.checkbox("Show Email Config Error", False):
                st.sidebar.error(f"Email setup error: {str(e)}")

def get_enhanced_technician_database() -> pd.DataFrame:
    """Enhanced technician database with notification preferences"""
    
    technicians = [
        {
            'id': 'TECH-001',
            'name': 'John Smith',
            'email': 'john.smith@company.com',
            'phone': '+1-555-0123',
            'shift': 'Day Shift',
            'skills': ['Mechanical', 'Electrical', 'Hydraulics'],
            'specialization': 'Pumps & Motors',
            'availability': 'Available',
            'workload': 2,
            'max_workload': 5,
            'notification_preferences': {
                'email': True,
                'sms': True,
                'priority_threshold': 'Medium'
            },
            'location': 'Building A',
            'experience_years': 8
        },
        {
            'id': 'TECH-002',
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@company.com',
            'phone': '+1-555-0124',
            'shift': 'Night Shift',
            'skills': ['Electrical', 'Controls', 'Automation'],
            'specialization': 'Control Systems',
            'availability': 'Available',
            'workload': 1,
            'max_workload': 4,
            'notification_preferences': {
                'email': True,
                'sms': True,
                'priority_threshold': 'High'
            },
            'location': 'Building B',
            'experience_years': 6
        },
        {
            'id': 'TECH-003',
            'name': 'Mike Rodriguez',
            'email': 'mike.rodriguez@company.com',
            'phone': '+1-555-0125',
            'shift': 'Day Shift',
            'skills': ['Mechanical', 'Welding', 'Fabrication'],
            'specialization': 'Heavy Machinery',
            'availability': 'Busy',
            'workload': 4,
            'max_workload': 5,
            'notification_preferences': {
                'email': True,
                'sms': False,
                'priority_threshold': 'Critical'
            },
            'location': 'Building A',
            'experience_years': 12
        },
        {
            'id': 'TECH-004',
            'name': 'Emily Chen',
            'email': 'emily.chen@company.com',
            'phone': '+1-555-0126',
            'shift': 'Weekend Shift',
            'skills': ['Electrical', 'Electronics', 'Instrumentation'],
            'specialization': 'Sensors & Instrumentation',
            'availability': 'Available',
            'workload': 0,
            'max_workload': 3,
            'notification_preferences': {
                'email': True,
                'sms': True,
                'priority_threshold': 'Low'
            },
            'location': 'Building C',
            'experience_years': 4
        }
    ]
    
    return pd.DataFrame(technicians)

def smart_technician_assignment(equipment_data: Dict, failure_probability: float) -> Dict:
    """Smart technician assignment based on skills, availability, and workload"""
    
    technicians_df = get_enhanced_technician_database()
    
    # Determine priority based on failure probability
    if failure_probability >= 90:
        priority = 'Critical'
    elif failure_probability >= 75:
        priority = 'High'
    elif failure_probability >= 50:
        priority = 'Medium'
    else:
        priority = 'Low'
    
    # Equipment type to skill mapping
    equipment_skill_map = {
        'pump': ['Mechanical', 'Hydraulics'],
        'motor': ['Mechanical', 'Electrical'],
        'conveyor': ['Mechanical', 'Electrical'],
        'compressor': ['Mechanical', 'Hydraulics'],
        'sensor': ['Electrical', 'Electronics', 'Instrumentation'],
        'control': ['Electrical', 'Controls', 'Automation']
    }
    
    # Get required skills for equipment
    equipment_type = equipment_data.get('type', '').lower()
    required_skills = []
    for eq_type, skills in equipment_skill_map.items():
        if eq_type in equipment_type:
            required_skills.extend(skills)
    
    if not required_skills:
        required_skills = ['Mechanical']  # Default skill
    
    # Filter technicians based on availability and skills
    available_techs = technicians_df[
        (technicians_df['availability'] == 'Available') |
        ((technicians_df['availability'] == 'Busy') & (priority in ['Critical', 'High']))
    ].copy()
    
    if available_techs.empty:
        # If no one available, get least busy technician
        available_techs = technicians_df.nsmallest(1, 'workload')
    
    # Score technicians based on skill match and workload
    def calculate_score(row):
        skill_match = len(set(required_skills) & set(row['skills'])) / len(required_skills)
        workload_score = 1 - (row['workload'] / row['max_workload'])
        experience_score = min(row['experience_years'] / 10, 1)  # Cap at 10 years
        
        # Priority bonus for less busy technicians on critical issues
        priority_bonus = 0
        if priority == 'Critical' and row['workload'] < 2:
            priority_bonus = 0.2
        
        return (skill_match * 0.4) + (workload_score * 0.3) + (experience_score * 0.2) + priority_bonus
    
    available_techs['assignment_score'] = available_techs.apply(calculate_score, axis=1)
    
    # Select best technician
    best_tech = available_techs.loc[available_techs['assignment_score'].idxmax()]
    
    return {
        'technician': best_tech.to_dict(),
        'priority': priority,
        'confidence': best_tech['assignment_score'],
        'assignment_reason': f"Best match based on skills: {', '.join(set(required_skills) & set(best_tech['skills']))}"
    }

def create_work_order_from_prediction(equipment_id: str, 
                                    failure_probability: float,
                                    prediction_details: Dict = None) -> Dict:
    """Create a work order from equipment failure prediction"""
    
    # Generate work order ID
    work_order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Determine priority and urgency
    if failure_probability >= 90:
        priority = 'Critical'
        urgency = 'Immediate'
        estimated_duration = '2-4 hours'
    elif failure_probability >= 75:
        priority = 'High'
        urgency = 'Within 4 hours'
        estimated_duration = '1-3 hours'
    elif failure_probability >= 50:
        priority = 'Medium'
        urgency = 'Within 24 hours'
        estimated_duration = '1-2 hours'
    else:
        priority = 'Low'
        urgency = 'Within 72 hours'
        estimated_duration = '30 minutes - 1 hour'
    
    # Generate description based on prediction details
    if prediction_details:
        description = f"Predictive model indicates {failure_probability}% probability of failure. "
        description += f"Key factors: {', '.join(prediction_details.get('risk_factors', ['General wear']))}"
        
        symptoms = ', '.join(prediction_details.get('symptoms', ['Automated detection']))
        recommended_action = prediction_details.get('recommended_action', 
                                                   'Inspect equipment and perform preventive maintenance')
    else:
        description = f"Predictive maintenance alert: {failure_probability}% failure probability detected."
        symptoms = "Automated predictive analysis indicates potential issues"
        recommended_action = "Perform comprehensive inspection and maintenance as needed"
    
    work_order = {
        'id': work_order_id,
        'equipment_id': equipment_id,
        'priority': priority,
        'urgency': urgency,
        'status': 'Open',
        'created_date': datetime.now(),
        'estimated_duration': estimated_duration,
        'description': description,
        'symptoms': symptoms,
        'recommended_action': recommended_action,
        'failure_probability': failure_probability,
        'prediction_details': prediction_details or {}
    }
    
    return work_order

def enhanced_maintenance_assignment_section(equipment_predictions: pd.DataFrame):
    """Enhanced maintenance assignment section with notifications"""
    
    st.header("🔧 Maintenance Assignment & Notifications")
    
    # Initialize notification system
    initialize_notification_system()
    
    # Display email configuration status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.get('email_configured', False):
            st.success("📧 Email notifications: Configured")
        else:
            st.warning("📧 Email notifications: Not configured")
    
    with col2:
        if st.button("🔧 Configure Email"):
            st.info("Please complete Phase 1 and 2 setup to configure email notifications")
    
    with col3:
        if st.button("📊 View History"):
            if st.session_state.get('notification_manager'):
                stats = st.session_state.notification_manager.get_notification_stats()
                st.metric("Notifications Sent", stats['total'])
    
    st.markdown("---")
    
    # Filter high-risk equipment
    high_risk_equipment = equipment_predictions[
        equipment_predictions['failure_probability'] >= 50
    ].sort_values('failure_probability', ascending=False)
    
    if high_risk_equipment.empty:
        st.info("✅ No high-risk equipment detected. All systems operating normally.")
        return
    
    st.subheader(f"⚠️ {len(high_risk_equipment)} Equipment Items Require Attention")
    
    # Display equipment requiring maintenance
    for idx, equipment in high_risk_equipment.iterrows():
        with st.expander(
            f"🚨 {equipment['equipment_id']} - {equipment['failure_probability']:.1f}% Risk",
            expanded=equipment['failure_probability'] >= 75
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Equipment details
                st.markdown(f"**Equipment ID:** {equipment['equipment_id']}")
                st.markdown(f"**Location:** {equipment.get('location', 'N/A')}")
                st.markdown(f"**Type:** {equipment.get('type', 'Industrial Equipment')}")
                st.markdown(f"**Failure Probability:** {equipment['failure_probability']:.1f}%")
                
                # Risk factors (if available)
                if 'risk_factors' in equipment:
                    st.markdown(f"**Risk Factors:** {', '.join(equipment['risk_factors'])}")
                
                # Create equipment data dict
                equipment_data = {
                    'equipment_id': equipment['equipment_id'],
                    'location': equipment.get('location', 'Production Floor'),
                    'type': equipment.get('type', 'Industrial Equipment'),
                    'failure_probability': equipment['failure_probability']
                }
                
                # Smart technician assignment
                assignment = smart_technician_assignment(equipment_data, equipment['failure_probability'])
                technician = assignment['technician']
                
                st.markdown("---")
                st.markdown("**🎯 Recommended Assignment:**")
                st.markdown(f"**Technician:** {technician['name']}")
                st.markdown(f"**Contact:** {technician['phone']} | {technician['email']}")
                st.markdown(f"**Shift:** {technician['shift']}")
                st.markdown(f"**Skills:** {', '.join(technician['skills'])}")
                st.markdown(f"**Specialization:** {technician['specialization']}")
                st.markdown(f"**Current Workload:** {technician['workload']}/{technician['max_workload']}")
                st.markdown(f"**Assignment Confidence:** {assignment['confidence']:.1%}")
                st.markdown(f"**Reason:** {assignment['assignment_reason']}")
            
            with col2:
                # Priority indicator
                priority_colors = {
                    'Critical': '🔴',
                    'High': '🟠', 
                    'Medium': '🟡',
                    'Low': '🟢'
                }
                
                st.markdown(f"### {priority_colors[assignment['priority']]} {assignment['priority']} Priority")
                
                # Action buttons
                if st.button(f"📋 Create Work Order", key=f"wo_{equipment['equipment_id']}"):
                    # Create work order
                    work_order = create_work_order_from_prediction(
                        equipment['equipment_id'],
                        equipment['failure_probability'],
                        equipment.to_dict()
                    )
                    
                    # Store in session state
                    if 'work_orders' not in st.session_state:
                        st.session_state.work_orders = []
                    
                    st.session_state.work_orders.append(work_order)
                    st.success(f"✅ Work Order {work_order['id']} created!")
                
                if st.button(f"📧 Send Notification", key=f"notify_{equipment['equipment_id']}"):
                    if not st.session_state.get('email_configured', False):
                        st.error("❌ Email not configured. Complete Phase 1 and 2 setup first.")
                    else:
                        # Create work order for notification
                        work_order = create_work_order_from_prediction(
                            equipment['equipment_id'],
                            equipment['failure_probability'],
                            equipment.to_dict()
                        )
                        
                        # Send notification
                        with st.spinner("Sending notification..."):
                            results = st.session_state.notification_manager.send_work_order_notification(
                                work_order,
                                technician,
                                equipment_data
                            )
                        
                        if results['email']['success']:
                            st.success(f"✅ Notification sent to {technician['name']}")
                            st.info(f"📧 Email: {technician['email']}")
                        else:
                            st.error(f"❌ Notification failed: {results['email']['message']}")
                
                # Manual assignment option
                if st.button(f"👤 Manual Assignment", key=f"manual_{equipment['equipment_id']}"):
                    with st.form(f"manual_form_{equipment['equipment_id']}"):
                        st.markdown("**Manual Technician Assignment:**")
                        
                        technicians_df = get_enhanced_technician_database()
                        selected_tech = st.selectbox(
                            "Select Technician:",
                            options=technicians_df['name'].tolist(),
                            key=f"select_tech_{equipment['equipment_id']}"
                        )
                        
                        custom_priority = st.selectbox(
                            "Override Priority:",
                            options=['Low', 'Medium', 'High', 'Critical'],
                            index=['Low', 'Medium', 'High', 'Critical'].index(assignment['priority']),
                            key=f"priority_{equipment['equipment_id']}"
                        )
                        
                        custom_notes = st.text_area(
                            "Additional Notes:",
                            key=f"notes_{equipment['equipment_id']}"
                        )
                        
                        if st.form_submit_button("📤 Assign & Notify"):
                            selected_technician = technicians_df[
                                technicians_df['name'] == selected_tech
                            ].iloc[0].to_dict()
                            
                            # Create custom work order
                            work_order = create_work_order_from_prediction(
                                equipment['equipment_id'],
                                equipment['failure_probability'],
                                equipment.to_dict()
                            )
                            work_order['priority'] = custom_priority
                            work_order['additional_notes'] = custom_notes
                            
                            if st.session_state.get('email_configured', False):
                                # Send notification
                                results = st.session_state.notification_manager.send_work_order_notification(
                                    work_order,
                                    selected_technician,
                                    equipment_data
                                )
                                
                                if results['email']['success']:
                                    st.success(f"✅ Work order assigned to {selected_tech} and notification sent!")
                                else:
                                    st.error(f"❌ Assignment created but notification failed: {results['email']['message']}")
                            else:
                                st.success(f"✅ Work order assigned to {selected_tech} (email notification not configured)")

def display_work_order_dashboard():
    """Display active work orders dashboard"""
    
    st.header("📋 Active Work Orders")
    
    if 'work_orders' not in st.session_state or not st.session_state.work_orders:
        st.info("📭 No active work orders. Create work orders from equipment predictions above.")
        return
    
    # Work order statistics
    work_orders = st.session_state.work_orders
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Work Orders", len(work_orders))
    
    with col2:
        critical_count = sum(1 for wo in work_orders if wo['priority'] == 'Critical')
        st.metric("Critical Priority", critical_count)
    
    with col3:
        open_count = sum(1 for wo in work_orders if wo['status'] == 'Open')
        st.metric("Open", open_count)
    
    with col4:
        avg_risk = sum(wo['failure_probability'] for wo in work_orders) / len(work_orders)
        st.metric("Avg Risk", f"{avg_risk:.1f}%")
    
    # Work orders table
    st.markdown("---")
    
    work_orders_df = pd.DataFrame([
        {
            'Work Order ID': wo['id'],
            'Equipment ID': wo['equipment_id'],
            'Priority': wo['priority'],
            'Status': wo['status'],
            'Risk %': f"{wo['failure_probability']:.1f}%",
            'Created': wo['created_date'].strftime('%Y-%m-%d %H:%M'),
            'Duration': wo['estimated_duration']
        }
        for wo in work_orders
    ])
    
    st.dataframe(
        work_orders_df,
        use_container_width=True,
        column_config={
            'Priority': st.column_config.SelectboxColumn(
                options=['Low', 'Medium', 'High', 'Critical']
            ),
            'Status': st.column_config.SelectboxColumn(
                options=['Open', 'In Progress', 'Completed', 'Cancelled']
            )
        }
    )

# Example usage function to add to your main dashboard
def integrate_with_existing_dashboard(equipment_predictions_df):
    """
    Integration function - call this in your main dashboard after equipment predictions
    
    Args:
        equipment_predictions_df: Your existing DataFrame with equipment predictions
    """
    
    # Add the enhanced assignment section
    enhanced_maintenance_assignment_section(equipment_predictions_df)
    
    st.markdown("---")
    
    # Add work order dashboard
    display_work_order_dashboard()
    
    # Add notification history in sidebar
    if st.sidebar.checkbox("📊 Show Notification History"):
        if st.session_state.get('notification_manager'):
            history = st.session_state.notification_manager.get_notification_history()
            if history:
                st.sidebar.markdown("### Recent Notifications")
                for notification in history[-5:]:  # Last 5
                    status = "✅" if notification['email']['success'] else "❌"
                    st.sidebar.markdown(f"{status} {notification['work_order_id']}")
            else:
                st.sidebar.info("No notifications sent yet")
        else:
            st.sidebar.warning("Email not configured")
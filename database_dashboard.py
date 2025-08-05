"""
Database-Powered Dashboard Components
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from database_integration import EquipmentDatabase
import sqlite3

class DatabaseDashboard:
    def __init__(self, db_path='equipment_monitoring.db'):
        """Initialize database dashboard"""
        self.db = EquipmentDatabase(db_path)
    
    def render_real_time_overview(self):
        """Render real-time overview using database"""
        st.header("🔴 Live Equipment Status")
        
        # Get current metrics from database
        metrics = self.db.get_dashboard_metrics()
        
        # Real-time metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Equipment", metrics['total_equipment'])
        
        with col2:
            active_alerts = metrics['active_alerts']
            st.metric("Active Alerts", active_alerts, 
                     delta=f"{'🚨' if active_alerts > 0 else '✅'}")
        
        with col3:
            upcoming_maintenance = metrics['upcoming_maintenance']
            st.metric("Upcoming Maintenance", upcoming_maintenance,
                     delta=f"Next 7 days")
        
        with col4:
            # Calculate current fleet health from latest predictions
            equipment_data = self.db.get_equipment_data()
            if not equipment_data.empty and 'health_score' in equipment_data.columns:
                avg_health = equipment_data['health_score'].mean()
                st.metric("Fleet Health", f"{avg_health:.1f}%")
            else:
                st.metric("Fleet Health", "N/A")
        
        # Risk distribution chart
        if metrics['risk_distribution']:
            st.subheader("📊 Current Risk Distribution")
            
            risk_df = pd.DataFrame(metrics['risk_distribution'])
            
            fig = px.pie(
                risk_df, 
                values='count', 
                names='risk_level',
                title="Equipment by Risk Level",
                color_discrete_map={
                    'Critical': '#ff4444',
                    'High': '#ff8800',
                    'Medium': '#ffcc00',
                    'Low': '#44ff44'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_equipment_history_analysis(self):
        """Render equipment history and trend analysis"""
        st.header("📈 Equipment History & Trends")
        
        # Equipment selector
        equipment_data = self.db.get_equipment_data()
        if equipment_data.empty:
            st.warning("No equipment data available")
            return
        
        equipment_options = equipment_data['equipment_id'].tolist()
        selected_equipment = st.selectbox("Select Equipment for Analysis", equipment_options)
        
        if selected_equipment:
            # Get equipment history
            history = self.db.get_equipment_history(selected_equipment, days_back=30)
            
            # Equipment info
            eq_info = equipment_data[equipment_data['equipment_id'] == selected_equipment].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📋 {selected_equipment} Details")
                st.write(f"**Type:** {eq_info.get('equipment_type', 'Unknown')}")
                st.write(f"**Location:** {eq_info.get('room_id', 'Unknown')}")
                st.write(f"**Age:** {eq_info.get('age_months', 'Unknown')} months")
                st.write(f"**Status:** {eq_info.get('status', 'Unknown')}")
            
            with col2:
                st.subheader("🎯 Current Status")
                if 'failure_probability' in eq_info and pd.notna(eq_info['failure_probability']):
                    st.metric("Failure Risk", f"{eq_info['failure_probability']:.3f}")
                if 'health_score' in eq_info and pd.notna(eq_info['health_score']):
                    st.metric("Health Score", f"{eq_info['health_score']:.1f}%")
                if 'risk_level' in eq_info and pd.notna(eq_info['risk_level']):
                    st.metric("Risk Level", eq_info['risk_level'])
            
            # Historical sensor data
            if not history['readings'].empty:
                st.subheader("📊 Sensor Data Trends (Last 30 Days)")
                
                readings_df = history['readings']
                readings_df['timestamp'] = pd.to_datetime(readings_df['timestamp'])
                
                # Create subplots for multiple metrics
                sensor_columns = ['operating_temperature', 'vibration_level', 'power_consumption', 'performance_score']
                available_sensors = [col for col in sensor_columns if col in readings_df.columns and readings_df[col].notna().any()]
                
                if available_sensors:
                    fig = make_subplots(
                        rows=len(available_sensors), cols=1,
                        subplot_titles=available_sensors,
                        vertical_spacing=0.1
                    )
                    
                    colors = ['blue', 'red', 'green', 'orange']
                    
                    for i, sensor in enumerate(available_sensors):
                        fig.add_trace(
                            go.Scatter(
                                x=readings_df['timestamp'],
                                y=readings_df[sensor],
                                mode='lines+markers',
                                name=sensor,
                                line=dict(color=colors[i % len(colors)])
                            ),
                            row=i+1, col=1
                        )
                    
                    fig.update_layout(height=200 * len(available_sensors), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Prediction history
            if not history['predictions'].empty:
                st.subheader("🔮 Prediction History")
                
                pred_df = history['predictions']
                pred_df['prediction_date'] = pd.to_datetime(pred_df['prediction_date'])
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=pred_df['prediction_date'],
                    y=pred_df['failure_probability'],
                    mode='lines+markers',
                    name='Failure Probability',
                    line=dict(color='red')
                ))
                
                if 'health_score' in pred_df.columns:
                    fig.add_trace(go.Scatter(
                        x=pred_df['prediction_date'],
                        y=pred_df['health_score'] / 100,  # Normalize to 0-1 scale
                        mode='lines+markers',
                        name='Health Score (normalized)',
                        line=dict(color='green'),
                        yaxis='y2'
                    ))
                
                fig.add_hline(y=0.7, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
                fig.add_hline(y=0.5, line_dash="dash", line_color="orange", annotation_text="High Risk Threshold")
                
                fig.update_layout(
                    title="Failure Probability Trend",
                    xaxis_title="Date",
                    yaxis_title="Failure Probability",
                    yaxis2=dict(title="Health Score", overlaying='y', side='right')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Maintenance history
            if not history['maintenance'].empty:
                st.subheader("🔧 Maintenance History")
                
                maint_df = history['maintenance']
                maint_df_display = maint_df[['work_order_id', 'maintenance_type', 'scheduled_date', 
                                           'completion_date', 'status', 'technician_name']].copy()
                
                st.dataframe(maint_df_display, use_container_width=True)
    
    def render_active_alerts_management(self):
        """Render active alerts with management capabilities"""
        st.header("🚨 Active Alerts Management")
        
        alerts_df = self.db.get_active_alerts()
        
        if alerts_df.empty:
            st.success("✅ No active alerts! All equipment is operating normally.")
            return
        
        st.warning(f"⚠️ {len(alerts_df)} active alerts require attention")
        
        # Display alerts
        for idx, alert in alerts_df.iterrows():
            with st.expander(f"🚨 Alert #{alert['id']} - {alert['equipment_id']} ({alert['alert_level'].upper()})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Equipment:** {alert['equipment_id']} ({alert['equipment_type']})")
                    st.write(f"**Location:** {alert['room_id']}")
                    st.write(f"**Message:** {alert['message']}")
                    st.write(f"**Created:** {alert['created_at']}")
                
                with col2:
                    st.metric("Alert Level", alert['alert_level'])
                    if pd.notna(alert['failure_probability']):
                        st.metric("Failure Risk", f"{alert['failure_probability']:.3f}")
                
                with col3:
                    # Acknowledge button
                    if st.button(f"✅ Acknowledge", key=f"ack_{alert['id']}"):
                        self.db.acknowledge_alert(alert['id'], "Dashboard User")
                        st.success("Alert acknowledged!")
                        st.rerun()
                    
                    # Quick action button
                    if st.button(f"🔧 Schedule Maintenance", key=f"maint_{alert['id']}"):
                        st.info("Redirecting to maintenance scheduling...")
                        # This would integrate with maintenance scheduling
    
    def render_maintenance_calendar(self):
        """Render maintenance calendar and scheduling"""
        st.header("📅 Maintenance Calendar")
        
        # Get maintenance schedule
        days_ahead = st.slider("Days to show", 7, 90, 30)
        schedule_df = self.db.get_maintenance_schedule(days_ahead)
        
        if schedule_df.empty:
            st.info("No maintenance scheduled for the selected period")
            return
        
        # Calendar view
        st.subheader(f"📋 Upcoming Maintenance ({len(schedule_df)} items)")
        
        # Group by date
        schedule_df['scheduled_date'] = pd.to_datetime(schedule_df['scheduled_date'])
        daily_schedule = schedule_df.groupby(schedule_df['scheduled_date'].dt.date)
        
        for date, day_schedule in daily_schedule:
            st.write(f"**{date.strftime('%A, %B %d, %Y')}**")
            
            for idx, item in day_schedule.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"🔧 {item['equipment_id']} - {item['maintenance_type']}")
                
                with col2:
                    st.write(f"👤 {item['technician_name']}")
                
                with col3:
                    st.write(f"💰 ${item['estimated_cost']:,.0f}" if pd.notna(item['estimated_cost']) else "N/A")
                
                with col4:
                    status_emoji = "🟡" if item['status'] == 'scheduled' else "🔄" if item['status'] == 'in_progress' else "✅"
                    st.write(f"{status_emoji} {item['status']}")
            
            st.markdown("---")
    
    def render_cost_analysis_dashboard(self):
        """Render cost analysis and ROI dashboard"""
        st.header("💰 Cost Analysis & ROI")
        
        # Get equipment data for analysis
        equipment_data = self.db.get_equipment_data()
        
        if equipment_data.empty:
            st.warning("No equipment data available for cost analysis")
            return
        
        # Calculate cost metrics
        total_equipment = len(equipment_data)
        
        # Estimated costs by risk level
        cost_by_risk = {
            'Critical': 1500,  # Emergency repair cost
            'High': 800,       # Urgent maintenance cost
            'Medium': 300,     # Preventive maintenance cost
            'Low': 100         # Routine inspection cost
        }
        
        total_estimated_cost = 0
        risk_breakdown = {}
        
        for risk_level, cost in cost_by_risk.items():
            count = len(equipment_data[equipment_data['risk_level'] == risk_level])
            risk_breakdown[risk_level] = {
                'count': count,
                'unit_cost': cost,
                'total_cost': count * cost
            }
            total_estimated_cost += count * cost
        
        # Display cost metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Maintenance Cost", f"${total_estimated_cost:,.0f}")
        
        with col2:
            # Calculate potential savings from preventive maintenance
            critical_cost = risk_breakdown['Critical']['total_cost']
            high_cost = risk_breakdown['High']['total_cost']
            preventive_cost = (risk_breakdown['Critical']['count'] + risk_breakdown['High']['count']) * 300
            potential_savings = critical_cost + high_cost - preventive_cost
            st.metric("Potential Savings", f"${potential_savings:,.0f}")
        
        with col3:
            roi = (potential_savings / preventive_cost * 100) if preventive_cost > 0 else 0
            st.metric("Maintenance ROI", f"{roi:.0f}%")
        
        # Cost breakdown chart
        st.subheader("📊 Cost Breakdown by Risk Level")
        
        cost_df = pd.DataFrame([
            {'Risk Level': level, 'Equipment Count': data['count'], 
             'Unit Cost': data['unit_cost'], 'Total Cost': data['total_cost']}
            for level, data in risk_breakdown.items()
            if data['count'] > 0
        ])
        
        fig = px.bar(
            cost_df, 
            x='Risk Level', 
            y='Total Cost',
            color='Risk Level',
            title="Estimated Maintenance Costs by Risk Level",
            color_discrete_map={
                'Critical': '#ff4444',
                'High': '#ff8800',
                'Medium': '#ffcc00', 
                'Low': '#44ff44'
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed cost table
        st.subheader("📋 Detailed Cost Analysis")
        st.dataframe(cost_df, use_container_width=True)

def render_database_dashboard():
    """Main function to render database-powered dashboard"""
    try:
        dashboard = DatabaseDashboard()
        
        # Check if database exists and has data
        equipment_data = dashboard.db.get_equipment_data()
        
        if equipment_data.empty:
            st.warning("⚠️ No equipment data found in database. Please run migration first.")
            st.code("python database_migration.py")
            return
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔴 Live Status", 
            "📈 Equipment History", 
            "🚨 Active Alerts",
            "📅 Maintenance Calendar",
            "💰 Cost Analysis"
        ])
        
        with tab1:
            dashboard.render_real_time_overview()
        
        with tab2:
            dashboard.render_equipment_history_analysis()
        
        with tab3:
            dashboard.render_active_alerts_management()
        
        with tab4:
            dashboard.render_maintenance_calendar()
        
        with tab5:
            dashboard.render_cost_analysis_dashboard()
    
    except Exception as e:
        st.error(f"Error loading database dashboard: {e}")
        st.info("Please ensure the database is initialized. Run: python database_migration.py")

if __name__ == "__main__":
    render_database_dashboard()

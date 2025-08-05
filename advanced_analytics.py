"""
Advanced Analytics Module for Equipment Failure Prediction
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

def create_trend_analysis(equipment_data):
    """Create trend analysis charts for equipment health over time"""
    
    # Simulate historical data for trend analysis
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    
    trend_data = []
    for equipment_type in equipment_data['equipment_type'].unique():
        base_health = equipment_data[equipment_data['equipment_type'] == equipment_type]['health_score'].mean()
        
        for date in dates:
            # Simulate seasonal variations and degradation
            seasonal_factor = 0.95 + 0.1 * np.sin(2 * np.pi * date.dayofyear / 365)
            degradation = (date - dates[0]).days / 365 * 0.05  # 5% degradation per year
            noise = np.random.normal(0, 2)
            
            health = base_health * seasonal_factor - degradation + noise
            health = max(0, min(100, health))  # Clamp between 0-100
            
            trend_data.append({
                'date': date,
                'equipment_type': equipment_type,
                'health_score': health,
                'failure_probability': max(0, min(1, (100 - health) / 100))
            })
    
    return pd.DataFrame(trend_data)

def create_predictive_maintenance_schedule(equipment_data):
    """Generate optimized maintenance schedule based on predictions"""
    
    maintenance_schedule = []
    
    for idx, row in equipment_data.iterrows():
        equipment_id = f"EQ-{idx:03d}"
        failure_prob = row['failure_probability']
        
        # Calculate optimal maintenance timing
        if failure_prob >= 0.7:
            days_to_maintenance = 7  # Critical - immediate
            maintenance_type = "Emergency Corrective"
        elif failure_prob >= 0.5:
            days_to_maintenance = 14  # High risk
            maintenance_type = "Scheduled Corrective"
        elif failure_prob >= 0.3:
            days_to_maintenance = 30  # Medium risk
            maintenance_type = "Preventive"
        else:
            days_to_maintenance = 90  # Low risk
            maintenance_type = "Routine Inspection"
        
        # Calculate cost estimates
        base_costs = {
            "Emergency Corrective": 1500,
            "Scheduled Corrective": 800,
            "Preventive": 300,
            "Routine Inspection": 100
        }
        
        cost_multiplier = 1.0
        if 'age_months' in row:
            cost_multiplier += (row['age_months'] / 120) * 0.5  # Older equipment costs more
        
        estimated_cost = base_costs[maintenance_type] * cost_multiplier
        
        maintenance_schedule.append({
            'equipment_id': equipment_id,
            'equipment_type': row['equipment_type'],
            'failure_probability': failure_prob,
            'maintenance_type': maintenance_type,
            'scheduled_date': datetime.now() + timedelta(days=days_to_maintenance),
            'estimated_cost': estimated_cost,
            'priority': 'Critical' if failure_prob >= 0.7 else 'High' if failure_prob >= 0.5 else 'Medium' if failure_prob >= 0.3 else 'Low'
        })
    
    return pd.DataFrame(maintenance_schedule)

def create_cost_benefit_analysis(equipment_data):
    """Calculate comprehensive cost-benefit analysis"""
    
    # Equipment failure costs by type
    failure_costs = {
        'Projector': 2000,
        'Air Conditioner': 3500,
        'Podium': 1200
    }
    
    # Maintenance costs by type
    maintenance_costs = {
        'Preventive': 300,
        'Corrective': 800,
        'Emergency': 1500
    }
    
    analysis = {
        'total_equipment': len(equipment_data),
        'at_risk_equipment': len(equipment_data[equipment_data['failure_probability'] >= 0.5]),
        'estimated_failure_cost': 0,
        'preventive_maintenance_cost': 0,
        'potential_savings': 0
    }
    
    for idx, row in equipment_data.iterrows():
        equipment_type = row['equipment_type']
        failure_prob = row['failure_probability']
        
        # Expected failure cost (probability × cost)
        expected_failure_cost = failure_prob * failure_costs.get(equipment_type, 2000)
        analysis['estimated_failure_cost'] += expected_failure_cost
        
        # Preventive maintenance cost
        if failure_prob >= 0.3:
            analysis['preventive_maintenance_cost'] += maintenance_costs['Preventive']
        
    analysis['potential_savings'] = analysis['estimated_failure_cost'] - analysis['preventive_maintenance_cost']
    analysis['roi_percentage'] = (analysis['potential_savings'] / analysis['preventive_maintenance_cost']) * 100 if analysis['preventive_maintenance_cost'] > 0 else 0
    
    return analysis

def render_advanced_analytics_page(equipment_data):
    """Render the advanced analytics page"""
    
    st.header("📊 Advanced Analytics & Insights")
    
    # Cost-Benefit Analysis
    st.subheader("💰 Cost-Benefit Analysis")
    cost_analysis = create_cost_benefit_analysis(equipment_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Equipment at Risk", cost_analysis['at_risk_equipment'], 
                 f"{cost_analysis['at_risk_equipment']/cost_analysis['total_equipment']*100:.1f}%")
    
    with col2:
        st.metric("Potential Failure Cost", f"${cost_analysis['estimated_failure_cost']:,.0f}")
    
    with col3:
        st.metric("Preventive Maintenance Cost", f"${cost_analysis['preventive_maintenance_cost']:,.0f}")
    
    with col4:
        st.metric("Potential Savings", f"${cost_analysis['potential_savings']:,.0f}",
                 f"ROI: {cost_analysis['roi_percentage']:.0f}%")
    
    # Predictive Maintenance Schedule
    st.subheader("📅 Optimized Maintenance Schedule")
    
    schedule_df = create_predictive_maintenance_schedule(equipment_data)
    
    # Priority breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        priority_counts = schedule_df['priority'].value_counts()
        fig_priority = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Maintenance Priority Distribution",
            color_discrete_map={
                'Critical': '#ff4444',
                'High': '#ff8800',
                'Medium': '#ffcc00',
                'Low': '#44ff44'
            }
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        # Cost by maintenance type
        cost_by_type = schedule_df.groupby('maintenance_type')['estimated_cost'].sum().reset_index()
        fig_cost = px.bar(
            cost_by_type,
            x='maintenance_type',
            y='estimated_cost',
            title="Estimated Costs by Maintenance Type",
            labels={'estimated_cost': 'Cost ($)', 'maintenance_type': 'Maintenance Type'}
        )
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # Detailed schedule table
    st.subheader("📋 Detailed Maintenance Schedule")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.selectbox("Priority Filter", ['All'] + list(schedule_df['priority'].unique()))
    
    with col2:
        equipment_filter = st.selectbox("Equipment Type Filter", ['All'] + list(schedule_df['equipment_type'].unique()))
    
    with col3:
        days_ahead = st.slider("Days Ahead", 7, 180, 30)
    
    # Apply filters
    filtered_schedule = schedule_df.copy()
    
    if priority_filter != 'All':
        filtered_schedule = filtered_schedule[filtered_schedule['priority'] == priority_filter]
    
    if equipment_filter != 'All':
        filtered_schedule = filtered_schedule[filtered_schedule['equipment_type'] == equipment_filter]
    
    # Filter by date range
    max_date = datetime.now() + timedelta(days=days_ahead)
    filtered_schedule = filtered_schedule[filtered_schedule['scheduled_date'] <= max_date]
    
    # Sort by priority and date
    priority_order = {'Critical': 1, 'High': 2, 'Medium': 3, 'Low': 4}
    filtered_schedule['priority_order'] = filtered_schedule['priority'].map(priority_order)
    filtered_schedule = filtered_schedule.sort_values(['priority_order', 'scheduled_date'])
    
    # Display table
    display_schedule = filtered_schedule[['equipment_id', 'equipment_type', 'maintenance_type', 
                                       'scheduled_date', 'estimated_cost', 'priority']].copy()
    display_schedule['scheduled_date'] = display_schedule['scheduled_date'].dt.strftime('%Y-%m-%d')
    display_schedule['estimated_cost'] = display_schedule['estimated_cost'].round(0).astype(int)
    
    st.dataframe(
        display_schedule,
        use_container_width=True,
        hide_index=True
    )
    
    # Download option
    csv = filtered_schedule.to_csv(index=False)
    st.download_button(
        label="📥 Download Schedule (CSV)",
        data=csv,
        file_name=f"maintenance_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    # Equipment Health Trends (Simulated)
    st.subheader("📈 Equipment Health Trends")
    
    trend_data = create_trend_analysis(equipment_data)
    
    # Average health by equipment type over time
    avg_trends = trend_data.groupby(['date', 'equipment_type'])['health_score'].mean().reset_index()
    
    fig_trends = px.line(
        avg_trends,
        x='date',
        y='health_score',
        color='equipment_type',
        title="Equipment Health Trends Over Time",
        labels={'health_score': 'Average Health Score (%)', 'date': 'Date'}
    )
    
    fig_trends.add_hline(y=70, line_dash="dash", line_color="orange", 
                        annotation_text="Warning Threshold (70%)")
    fig_trends.add_hline(y=50, line_dash="dash", line_color="red",
                        annotation_text="Critical Threshold (50%)")
    
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # Predictive Insights
    st.subheader("🔮 Predictive Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Key Insights:**")
        
        high_risk_equipment = len(equipment_data[equipment_data['failure_probability'] >= 0.5])
        total_equipment = len(equipment_data)
        
        insights = [
            f"• {high_risk_equipment} out of {total_equipment} equipment items need attention",
            f"• Potential cost savings: ${cost_analysis['potential_savings']:,.0f}",
            f"• ROI from preventive maintenance: {cost_analysis['roi_percentage']:.0f}%",
            f"• Average fleet health: {equipment_data['health_score'].mean():.1f}%"
        ]
        
        for insight in insights:
            st.markdown(insight)
    
    with col2:
        st.markdown("**🎯 Recommendations:**")
        
        recommendations = [
            "• Prioritize critical and high-risk equipment for immediate maintenance",
            "• Implement weekly health monitoring for at-risk equipment",
            "• Consider equipment replacement for consistently poor performers",
            "• Establish preventive maintenance schedules to reduce emergency repairs"
        ]
        
        for rec in recommendations:
            st.markdown(rec)

if __name__ == "__main__":
    # This can be imported and used in the main dashboard
    pass

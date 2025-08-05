"""
Mobile-Responsive Dashboard Components
====================================

Enhanced Streamlit components optimized for mobile devices and responsive design.

Features:
- Mobile-first design approach
- Touch-friendly interface elements
- Responsive layouts
- Optimized data display for small screens
- Progressive web app (PWA) capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Custom CSS for mobile responsiveness
MOBILE_CSS = """
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .stMetric {
            background-color: #f0f2f6;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .equipment-card {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #4CAF50;
        }
        
        .equipment-card.critical {
            border-left-color: #f44336;
        }
        
        .equipment-card.high {
            border-left-color: #ff9800;
        }
        
        .equipment-card.medium {
            border-left-color: #ffeb3b;
        }
        
        .alert-banner {
            background: linear-gradient(90deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.8; }
            100% { opacity: 1; }
        }
        
        .technician-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            border: 1px solid #dee2e6;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background-color: #28a745; }
        .status-busy { background-color: #ffc107; }
        .status-offline { background-color: #dc3545; }
        
        .quick-action-btn {
            background: linear-gradient(45deg, #2196F3, #1976D2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: bold;
            margin: 5px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .quick-action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        
        .progress-bar {
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 8px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
    }
    
    /* Tablet styles */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
        }
    }
    
    /* Desktop styles */
    @media (min-width: 1025px) {
        .main .block-container {
            max-width: 1200px;
            margin: 0 auto;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .equipment-card {
            background: #2d3748;
            color: #e2e8f0;
        }
        
        .technician-card {
            background: #4a5568;
            color: #e2e8f0;
            border-color: #718096;
        }
    }
    
    /* Touch-friendly buttons */
    .stButton > button {
        min-height: 44px;
        min-width: 44px;
        font-size: 16px;
        border-radius: 8px;
        border: none;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Improved selectbox for mobile */
    .stSelectbox > div > div {
        min-height: 44px;
    }
    
    /* Better spacing for mobile */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Responsive charts */
    .plotly-graph-div {
        width: 100% !important;
        height: auto !important;
    }
</style>
"""

class MobileOptimizedDashboard:
    """Mobile-optimized dashboard components"""
    
    def __init__(self):
        # Inject mobile CSS
        st.markdown(MOBILE_CSS, unsafe_allow_html=True)
        
        # Set up responsive page config
        if 'mobile_mode' not in st.session_state:
            st.session_state.mobile_mode = self._detect_mobile()
    
    def _detect_mobile(self):
        """Detect if user is on mobile device"""
        # This is a simplified detection - in production, use JavaScript
        return st.session_state.get('is_mobile', False)
    
    def render_mobile_header(self, title: str, subtitle: str = ""):
        """Render mobile-optimized header"""
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 1rem;">
            <h1 style="margin: 0; font-size: 1.8rem;">{title}</h1>
            {f'<p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def render_metric_cards(self, metrics: dict):
        """Render mobile-optimized metric cards"""
        if st.session_state.get('mobile_mode', False):
            # Mobile: Single column layout
            for label, data in metrics.items():
                value = data.get('value', 0)
                delta = data.get('delta', None)
                color = data.get('color', '#667eea')
                
                delta_html = ""
                if delta is not None:
                    delta_color = "#28a745" if delta >= 0 else "#dc3545"
                    delta_symbol = "↗" if delta >= 0 else "↘"
                    delta_html = f'<span style="color: {delta_color}; font-size: 0.9rem;">{delta_symbol} {delta}</span>'
                
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);">
                    <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">{label}</h3>
                    <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{value}</div>
                    {delta_html}
                </div>
                """, unsafe_allow_html=True)
        else:
            # Desktop: Multi-column layout
            cols = st.columns(len(metrics))
            for idx, (label, data) in enumerate(metrics.items()):
                with cols[idx]:
                    value = data.get('value', 0)
                    delta = data.get('delta', None)
                    st.metric(label, value, delta)
    
    def render_equipment_card(self, equipment: dict, show_actions: bool = True):
        """Render mobile-optimized equipment card"""
        risk_level = equipment.get('risk_level', 'Low').lower()
        risk_colors = {
            'critical': '#f44336',
            'high': '#ff9800', 
            'medium': '#ffeb3b',
            'low': '#4CAF50'
        }
        
        risk_color = risk_colors.get(risk_level, '#4CAF50')
        risk_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
        
        actions_html = ""
        if show_actions:
            actions_html = """
            <div style="margin-top: 1rem;">
                <button class="quick-action-btn" onclick="scheduleMaintenanceAction()">📅 Schedule</button>
                <button class="quick-action-btn" onclick="viewDetailsAction()">👁️ Details</button>
            </div>
            """
        
        health_score = equipment.get('health_score', 0)
        progress_width = f"{health_score}%"
        
        st.markdown(f"""
        <div class="equipment-card {risk_level}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="margin: 0; color: #333;">{equipment.get('equipment_id', 'Unknown')}</h4>
                <span style="font-size: 1.2rem;">{risk_emoji.get(risk_level, '⚪')}</span>
            </div>
            
            <div style="color: #666; margin-bottom: 0.5rem;">
                <strong>{equipment.get('equipment_type', 'Unknown Type')}</strong><br>
                Location: {equipment.get('location', 'Unknown')}<br>
                Last Maintenance: {equipment.get('last_maintenance_days', 0)} days ago
            </div>
            
            <div style="margin-bottom: 0.5rem;">
                <small style="color: #666;">Health Score</small>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress_width};"></div>
                </div>
                <div style="text-align: center; font-weight: bold; color: {risk_color};">
                    {health_score:.1f}% - {risk_level.title()} Risk
                </div>
            </div>
            
            {actions_html}
        </div>
        """, unsafe_allow_html=True)
    
    def render_technician_status(self, technicians: dict):
        """Render mobile-optimized technician status"""
        st.subheader("👷‍♂️ Technician Status")
        
        for tech_id, tech_info in technicians.items():
            status = tech_info.get('availability', 'offline').lower()
            status_colors = {
                'available': '#28a745',
                'busy': '#ffc107',
                'offline': '#dc3545'
            }
            
            workload = tech_info.get('current_workload', 0)
            capacity = tech_info.get('max_capacity', 40)
            workload_percent = (workload / capacity * 100) if capacity > 0 else 0
            
            st.markdown(f"""
            <div class="technician-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="status-indicator status-{status.replace('available', 'online')}"></span>
                        <strong>{tech_info.get('name', 'Unknown')}</strong>
                    </div>
                    <div style="text-align: right; font-size: 0.9rem;">
                        <div>Workload: {workload}/{capacity}h</div>
                        <div style="color: #666;">{workload_percent:.0f}% utilized</div>
                    </div>
                </div>
                <div style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">
                    {', '.join(tech_info.get('specializations', []))}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_alert_banner(self, alert_count: int):
        """Render mobile-optimized alert banner"""
        if alert_count > 0:
            st.markdown(f"""
            <div class="alert-banner">
                <strong>🚨 {alert_count} CRITICAL ALERT{'S' if alert_count > 1 else ''}</strong><br>
                Immediate attention required
            </div>
            """, unsafe_allow_html=True)
    
    def render_mobile_chart(self, data: pd.DataFrame, chart_type: str = "bar", title: str = ""):
        """Render mobile-optimized charts"""
        # Configure for mobile display
        mobile_config = {
            'displayModeBar': False,
            'staticPlot': st.session_state.get('mobile_mode', False)
        }
        
        if chart_type == "bar":
            fig = px.bar(
                data, 
                title=title,
                height=300 if st.session_state.get('mobile_mode', False) else 400
            )
        elif chart_type == "pie":
            fig = px.pie(
                data,
                title=title,
                height=300 if st.session_state.get('mobile_mode', False) else 400
            )
        elif chart_type == "line":
            fig = px.line(
                data,
                title=title,
                height=300 if st.session_state.get('mobile_mode', False) else 400
            )
        
        # Mobile-specific layout adjustments
        fig.update_layout(
            title_font_size=14 if st.session_state.get('mobile_mode', False) else 16,
            font_size=10 if st.session_state.get('mobile_mode', False) else 12,
            margin=dict(l=20, r=20, t=40, b=20) if st.session_state.get('mobile_mode', False) else dict(l=40, r=40, t=60, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True, config=mobile_config)
    
    def render_quick_actions(self):
        """Render mobile-optimized quick action buttons"""
        st.markdown("### ⚡ Quick Actions")
        
        if st.session_state.get('mobile_mode', False):
            # Mobile: Vertical layout
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 View Alerts", use_container_width=True):
                    st.session_state.current_view = 'alerts'
                if st.button("📊 Fleet Status", use_container_width=True):
                    st.session_state.current_view = 'fleet'
            with col2:
                if st.button("🔧 Schedule Maintenance", use_container_width=True):
                    st.session_state.current_view = 'maintenance'
                if st.button("👥 Technicians", use_container_width=True):
                    st.session_state.current_view = 'technicians'
        else:
            # Desktop: Horizontal layout
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("🚨 View Alerts"):
                    st.session_state.current_view = 'alerts'
            with col2:
                if st.button("📊 Fleet Status"):
                    st.session_state.current_view = 'fleet'
            with col3:
                if st.button("🔧 Schedule Maintenance"):
                    st.session_state.current_view = 'maintenance'
            with col4:
                if st.button("👥 Technicians"):
                    st.session_state.current_view = 'technicians'
    
    def render_responsive_data_table(self, data: pd.DataFrame, max_rows: int = 10):
        """Render mobile-optimized data table"""
        if st.session_state.get('mobile_mode', False):
            # Mobile: Card-based display
            st.markdown("### 📋 Equipment List")
            
            # Show only essential columns for mobile
            display_cols = ['equipment_id', 'equipment_type', 'risk_level', 'health_score']
            available_cols = [col for col in display_cols if col in data.columns]
            
            for idx, row in data.head(max_rows).iterrows():
                equipment_data = {
                    'equipment_id': row.get('equipment_id', f'EQ-{idx:03d}'),
                    'equipment_type': row.get('equipment_type', 'Unknown'),
                    'risk_level': row.get('risk_level', 'Low'),
                    'health_score': row.get('health_score', 0),
                    'location': row.get('location', 'Unknown'),
                    'last_maintenance_days': row.get('last_maintenance_days', 0)
                }
                self.render_equipment_card(equipment_data, show_actions=False)
            
            if len(data) > max_rows:
                st.info(f"Showing {max_rows} of {len(data)} items. Use filters to narrow results.")
        else:
            # Desktop: Standard table
            st.dataframe(data, use_container_width=True)
    
    def render_mobile_navigation(self):
        """Render mobile-optimized navigation"""
        if st.session_state.get('mobile_mode', False):
            # Mobile: Bottom navigation style
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            nav_options = {
                'Dashboard': ('📊', 'dashboard'),
                'Equipment': ('🏭', 'equipment'),
                'Alerts': ('🚨', 'alerts'),
                'Profile': ('👤', 'profile')
            }
            
            for idx, (label, (icon, view)) in enumerate(nav_options.items()):
                col = [col1, col2, col3, col4][idx]
                with col:
                    if st.button(f"{icon}\n{label}", key=f"nav_{view}", use_container_width=True):
                        st.session_state.current_view = view
                        st.rerun()
        else:
            # Desktop: Sidebar navigation (existing)
            return self._render_desktop_navigation()
    
    def _render_desktop_navigation(self):
        """Render desktop navigation"""
        st.sidebar.title("🎛️ Navigation")
        
        view_options = {
            'dashboard': '📊 Main Dashboard',
            'equipment': '🏭 Equipment View',
            'alerts': '🚨 Alert Management',
            'maintenance': '🔧 Maintenance Log',
            'technicians': '👥 Technician Management',
            'analytics': '📈 Advanced Analytics'
        }
        
        selected_view = st.sidebar.radio(
            "Select View:",
            list(view_options.keys()),
            format_func=lambda x: view_options[x],
            index=list(view_options.keys()).index(st.session_state.get('current_view', 'dashboard'))
        )
        
        if selected_view != st.session_state.get('current_view', 'dashboard'):
            st.session_state.current_view = selected_view
            st.rerun()
        
        return selected_view

# Progressive Web App (PWA) components
def add_pwa_support():
    """Add Progressive Web App support"""
    
    # Manifest JSON
    manifest = {
        "name": "Equipment Failure Prediction System",
        "short_name": "EquipmentMonitor",
        "description": "Monitor and predict equipment failures",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#667eea",
        "icons": [
            {
                "src": "icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "icon-512.png", 
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    # Add manifest and service worker
    st.markdown(f"""
    <link rel="manifest" href="data:application/json;base64,{st._base64.b64encode(str(manifest).encode()).decode()}">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Equipment Monitor">
    """, unsafe_allow_html=True)

# Usage example
def demo_mobile_dashboard():
    """Demo of mobile-optimized dashboard"""
    mobile_dash = MobileOptimizedDashboard()
    
    # Header
    mobile_dash.render_mobile_header(
        "Equipment Monitor", 
        "Real-time equipment health tracking"
    )
    
    # Metrics
    metrics = {
        "Total Equipment": {"value": "1,250", "delta": "+12", "color": "#667eea"},
        "Critical Alerts": {"value": "3", "delta": "-2", "color": "#f44336"},
        "Fleet Health": {"value": "87%", "delta": "+5%", "color": "#4CAF50"},
        "Efficiency": {"value": "94%", "delta": "+2%", "color": "#ff9800"}
    }
    mobile_dash.render_metric_cards(metrics)
    
    # Alert banner
    mobile_dash.render_alert_banner(3)
    
    # Equipment cards
    st.subheader("🚨 High Priority Equipment")
    
    sample_equipment = [
        {
            "equipment_id": "EQ-001",
            "equipment_type": "Air Conditioner",
            "risk_level": "critical",
            "health_score": 23.5,
            "location": "Building A - Zone 1",
            "last_maintenance_days": 45
        },
        {
            "equipment_id": "EQ-015",
            "equipment_type": "Projector",
            "risk_level": "high",
            "health_score": 45.2,
            "location": "Conference Room B",
            "last_maintenance_days": 67
        }
    ]
    
    for equipment in sample_equipment:
        mobile_dash.render_equipment_card(equipment)
    
    # Quick actions
    mobile_dash.render_quick_actions()
    
    # Navigation
    mobile_dash.render_mobile_navigation()

if __name__ == "__main__":
    demo_mobile_dashboard()

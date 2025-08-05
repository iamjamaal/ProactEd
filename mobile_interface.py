"""
Mobile-Responsive Components for Equipment Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def apply_mobile_styling():
    """Apply mobile-responsive CSS styling"""
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    @media screen and (max-width: 768px) {
        .stApp > header {
            display: none;
        }
        
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Responsive metrics */
        .metric-container {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Mobile navigation */
        .mobile-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #ddd;
            padding: 0.5rem;
            z-index: 1000;
        }
        
        /* Responsive tables */
        .dataframe {
            font-size: 12px;
            overflow-x: auto;
        }
        
        /* Alert cards */
        .alert-card {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .alert-critical {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        
        .alert-high {
            background: #fff3cd;
            border-color: #ffeeba;
        }
        
        /* Equipment cards */
        .equipment-card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Quick action buttons */
        .quick-action-btn {
            background: #007bff;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            font-size: 14px;
            cursor: pointer;
        }
        
        /* Hide sidebar on mobile */
        .css-1d391kg {
            display: none;
        }
        
        /* Mobile chart adjustments */
        .plotly-graph-div {
            width: 100% !important;
            height: 300px !important;
        }
    }
    
    /* Tablet styles */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
        }
        
        .plotly-graph-div {
            height: 400px !important;
        }
    }
    
    /* Desktop styles */
    @media screen and (min-width: 1025px) {
        .plotly-graph-div {
            height: 500px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_mobile_navigation():
    """Render mobile-friendly navigation"""
    if st.sidebar.button("📱 Mobile View"):
        st.session_state.mobile_mode = True
    
    if st.session_state.get('mobile_mode', False):
        # Mobile navigation bar at bottom
        st.markdown("""
        <div class="mobile-nav">
            <div style="display: flex; justify-content: space-around;">
                <div style="text-align: center;">
                    <div style="font-size: 20px;">📊</div>
                    <div style="font-size: 10px;">Dashboard</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 20px;">🚨</div>
                    <div style="font-size: 10px;">Alerts</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 20px;">🔧</div>
                    <div style="font-size: 10px;">Maintenance</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 20px;">📋</div>
                    <div style="font-size: 10px;">Reports</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add bottom padding to prevent content overlap
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

def render_mobile_metrics(metrics):
    """Render metrics in mobile-friendly format"""
    # Single column layout for mobile
    for metric_name, metric_value in metrics.items():
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-size: 24px; font-weight: bold; color: #333;">
                {metric_value}
            </div>
            <div style="font-size: 14px; color: #666;">
                {metric_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_mobile_equipment_list(equipment_data):
    """Render equipment list in mobile-friendly cards"""
    for idx, equipment in equipment_data.iterrows():
        equipment_id = f"EQ-{idx:03d}"
        risk_level = equipment.get('risk_level', 'Unknown')
        failure_prob = equipment.get('failure_probability', 0)
        
        # Risk level styling
        risk_colors = {
            'Critical': '#ff4444',
            'High': '#ff8800',
            'Medium': '#ffcc00',
            'Low': '#44ff44'
        }
        
        risk_color = risk_colors.get(risk_level, '#999999')
        
        st.markdown(f"""
        <div class="equipment-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-weight: bold; font-size: 16px;">
                    {equipment_id}
                </div>
                <div style="background: {risk_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 12px;">
                    {risk_level}
                </div>
            </div>
            
            <div style="margin-bottom: 0.5rem;">
                <div style="font-size: 14px; color: #666;">
                    Type: {equipment.get('equipment_type', 'Unknown')}
                </div>
                <div style="font-size: 14px; color: #666;">
                    Location: {equipment.get('room_id', 'Unknown')}
                </div>
                <div style="font-size: 14px; color: #666;">
                    Failure Risk: {failure_prob:.1%}
                </div>
            </div>
            
            <div style="display: flex; gap: 0.5rem;">
                <button class="quick-action-btn" onclick="alert('View Details for {equipment_id}')">
                    👁️ View
                </button>
                <button class="quick-action-btn" onclick="alert('Schedule Maintenance for {equipment_id}')">
                    🔧 Maintain
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_mobile_alerts(alerts_data):
    """Render alerts in mobile-friendly format"""
    for alert in alerts_data:
        alert_class = "alert-critical" if alert['level'] == 'Critical' else "alert-high"
        
        st.markdown(f"""
        <div class="alert-card {alert_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-weight: bold;">
                    🚨 {alert['equipment_id']}
                </div>
                <div style="font-size: 12px; color: #666;">
                    {alert['timestamp']}
                </div>
            </div>
            
            <div style="margin-bottom: 0.5rem;">
                <div style="font-size: 14px;">
                    {alert['message']}
                </div>
            </div>
            
            <div style="display: flex; gap: 0.5rem;">
                <button class="quick-action-btn" style="background: #28a745;">
                    ✅ Acknowledge
                </button>
                <button class="quick-action-btn" style="background: #ffc107; color: black;">
                    🔧 Action
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_mobile_chart(df, chart_type='bar'):
    """Render mobile-optimized charts"""
    if chart_type == 'bar':
        fig = px.bar(
            df, 
            x='category', 
            y='value',
            title="Equipment Status",
            height=300  # Fixed height for mobile
        )
        
        # Mobile-specific layout adjustments
        fig.update_layout(
            title_font_size=14,
            font_size=10,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        
        # Adjust axis labels for mobile
        fig.update_xaxes(tickangle=45, tickfont_size=10)
        fig.update_yaxes(tickfont_size=10)
        
    elif chart_type == 'pie':
        fig = px.pie(
            df,
            values='value',
            names='category',
            title="Risk Distribution",
            height=300
        )
        
        fig.update_layout(
            title_font_size=14,
            font_size=10,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font_size=10
            )
        )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def render_mobile_dashboard():
    """Render complete mobile dashboard"""
    apply_mobile_styling()
    
    # Check if in mobile mode
    is_mobile = st.session_state.get('mobile_mode', False)
    
    if is_mobile:
        st.title("📱 Equipment Monitor")
        
        # Quick stats in mobile format
        st.subheader("📊 Status Overview")
        
        mobile_metrics = {
            "Total Equipment": "1,247",
            "At Risk": "23",
            "Active Alerts": "5",
            "Maintenance Due": "12"
        }
        
        render_mobile_metrics(mobile_metrics)
        
        # Quick alerts section
        st.subheader("🚨 Critical Alerts")
        
        sample_alerts = [
            {
                'equipment_id': 'EQ-001',
                'level': 'Critical',
                'message': 'High temperature detected - immediate attention required',
                'timestamp': '2 min ago'
            },
            {
                'equipment_id': 'EQ-045',
                'level': 'High',
                'message': 'Vibration levels above normal - schedule maintenance',
                'timestamp': '15 min ago'
            }
        ]
        
        render_mobile_alerts(sample_alerts)
        
        # Equipment status chart
        st.subheader("📈 Equipment Status")
        
        chart_data = pd.DataFrame({
            'category': ['Operational', 'At Risk', 'Critical', 'Maintenance'],
            'value': [1200, 23, 5, 19]
        })
        
        render_mobile_chart(chart_data, 'pie')
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Equipment", use_container_width=True):
                st.info("Equipment search feature")
        
        with col2:
            if st.button("📋 View Reports", use_container_width=True):
                st.info("Reports feature")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("🔧 Schedule Maintenance", use_container_width=True):
                st.info("Maintenance scheduling")
        
        with col4:
            if st.button("📞 Contact Support", use_container_width=True):
                st.info("Support contact")
        
        # Render mobile navigation
        render_mobile_navigation()
    
    else:
        # Regular desktop view
        st.info("Switch to mobile view using the sidebar")
        st.button("📱 Enable Mobile View", on_click=lambda: setattr(st.session_state, 'mobile_mode', True))

def render_progressive_web_app():
    """Enable Progressive Web App features"""
    st.markdown("""
    <script>
    // Service Worker Registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(error => console.log('SW registration failed'));
    }
    
    // Add to Home Screen prompt
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Show install button
        const installBtn = document.createElement('button');
        installBtn.textContent = '📱 Install App';
        installBtn.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 10px 20px;
            cursor: pointer;
            z-index: 1000;
        `;
        
        installBtn.addEventListener('click', () => {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                }
                deferredPrompt = null;
                installBtn.remove();
            });
        });
        
        document.body.appendChild(installBtn);
    });
    
    // Offline functionality
    window.addEventListener('online', () => {
        console.log('Online');
        // Sync data when back online
    });
    
    window.addEventListener('offline', () => {
        console.log('Offline');
        // Show offline indicator
    });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_mobile_dashboard()
    render_progressive_web_app()

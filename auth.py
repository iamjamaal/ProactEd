"""
Authentication and Authorization System
=====================================

Provides user authentication and role-based access control for the Equipment Failure Prediction System.

Features:
- User authentication with session management
- Role-based access control (Admin, Technician, Viewer)
- Secure password handling
- Activity logging
- Session timeout management

Usage:
    from auth import AuthManager, require_role
    
    auth = AuthManager()
    
    # In Streamlit app
    if not auth.is_authenticated():
        auth.show_login()
    else:
        # Show main app
        pass
"""

import streamlit as st
import hashlib
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Any
import secrets

class User:
    """User class for authentication system"""
    
    def __init__(self, username: str, password_hash: str, role: str, email: str = "", full_name: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.email = email
        self.full_name = full_name
        self.created_at = datetime.now()
        self.last_login = None
        self.login_count = 0
        self.is_active = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        user = cls(
            username=data['username'],
            password_hash=data['password_hash'],
            role=data['role'],
            email=data.get('email', ''),
            full_name=data.get('full_name', '')
        )
        
        if data.get('created_at'):
            user.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_login'):
            user.last_login = datetime.fromisoformat(data['last_login'])
        
        user.login_count = data.get('login_count', 0)
        user.is_active = data.get('is_active', True)
        
        return user

class AuthManager:
    """Authentication and authorization manager"""
    
    ROLES = {
        'admin': {
            'permissions': ['view_all', 'edit_all', 'manage_users', 'system_config'],
            'description': 'Full system access'
        },
        'technician': {
            'permissions': ['view_equipment', 'update_maintenance', 'view_assignments'],
            'description': 'Maintenance operations'
        },
        'supervisor': {
            'permissions': ['view_all', 'assign_technicians', 'approve_maintenance'],
            'description': 'Maintenance supervision'
        },
        'viewer': {
            'permissions': ['view_dashboard', 'view_reports'],
            'description': 'Read-only access'
        }
    }
    
    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=8)  # 8 hour session timeout
        
        self._load_users()
        self._initialize_default_users()
    
    def _load_users(self):
        """Load users from file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                
                for username, user_data in users_data.items():
                    self.users[username] = User.from_dict(user_data)
                    
            except Exception as e:
                st.error(f"Error loading users: {e}")
    
    def _save_users(self):
        """Save users to file"""
        try:
            users_data = {username: user.to_dict() for username, user in self.users.items()}
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
                
        except Exception as e:
            st.error(f"Error saving users: {e}")
    
    def _initialize_default_users(self):
        """Initialize default users if none exist"""
        if not self.users:
            # Create default admin user
            admin_password = "admin123"  # Should be changed on first login
            self.create_user(
                username="admin",
                password=admin_password,
                role="admin",
                email="admin@equipment-monitoring.com",
                full_name="System Administrator"
            )
            
            # Create default technician user
            tech_password = "tech123"
            self.create_user(
                username="technician",
                password=tech_password,
                role="technician",
                email="tech@equipment-monitoring.com",
                full_name="Maintenance Technician"
            )
            
            # Create default viewer user
            viewer_password = "viewer123"
            self.create_user(
                username="viewer",
                password=viewer_password,
                role="viewer",
                email="viewer@equipment-monitoring.com",
                full_name="Dashboard Viewer"
            )
            
            st.warning("⚠️ Default users created. Please change passwords immediately!")
            st.info(f"👤 Admin: admin/{admin_password} | 🔧 Technician: technician/{tech_password} | 👀 Viewer: viewer/{viewer_password}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == hash_hex
        except Exception:
            return False
    
    def create_user(self, username: str, password: str, role: str, email: str = "", full_name: str = "") -> bool:
        """Create a new user"""
        if username in self.users:
            return False
        
        if role not in self.ROLES:
            return False
        
        password_hash = self._hash_password(password)
        user = User(username, password_hash, role, email, full_name)
        
        self.users[username] = user
        self._save_users()
        
        return True
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        if not user.is_active:
            return False
        
        if self._verify_password(password, user.password_hash):
            # Update login info
            user.last_login = datetime.now()
            user.login_count += 1
            self._save_users()
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                'username': username,
                'login_time': datetime.now(),
                'last_activity': datetime.now()
            }
            
            # Store session in streamlit session state
            st.session_state['session_id'] = session_id
            st.session_state['username'] = username
            st.session_state['user_role'] = user.role
            st.session_state['authenticated'] = True
            
            return True
        
        return False
    
    def logout(self):
        """Logout current user"""
        if 'session_id' in st.session_state:
            session_id = st.session_state['session_id']
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        # Clear session state
        for key in ['session_id', 'username', 'user_role', 'authenticated']:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if current user is authenticated"""
        if not st.session_state.get('authenticated', False):
            return False
        
        session_id = st.session_state.get('session_id')
        if not session_id or session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Check session timeout
        if datetime.now() - session['last_activity'] > self.session_timeout:
            self.logout()
            return False
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        return True
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        if not self.is_authenticated():
            return None
        
        username = st.session_state.get('username')
        return self.users.get(username)
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        user = self.get_current_user()
        if not user:
            return False
        
        role_permissions = self.ROLES.get(user.role, {}).get('permissions', [])
        return permission in role_permissions
    
    def show_login(self):
        """Show login form"""
        st.title("🔐 Equipment Monitoring System")
        st.markdown("**Please login to access the system**")
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### Login")
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                
                submit_button = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit_button:
                    if username and password:
                        if self.authenticate(username, password):
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.warning("⚠️ Please enter both username and password")
        
        # Show default credentials info
        with st.expander("ℹ️ Default Login Credentials", expanded=False):
            st.markdown("""
            **Default Users:**
            - **Admin:** admin / admin123
            - **Technician:** technician / tech123  
            - **Viewer:** viewer / viewer123
            
            ⚠️ **Please change default passwords after first login!**
            """)
    
    def show_user_management(self):
        """Show user management interface (admin only)"""
        if not self.has_permission('manage_users'):
            st.error("❌ Access denied. Admin privileges required.")
            return
        
        st.header("👥 User Management")
        
        # Create new user
        with st.expander("➕ Create New User", expanded=False):
            with st.form("create_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username")
                    new_email = st.text_input("Email")
                    new_role = st.selectbox("Role", list(self.ROLES.keys()))
                
                with col2:
                    new_password = st.text_input("Password", type="password")
                    new_full_name = st.text_input("Full Name")
                
                create_button = st.form_submit_button("Create User")
                
                if create_button:
                    if new_username and new_password:
                        if self.create_user(new_username, new_password, new_role, new_email, new_full_name):
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create user. Username may already exist.")
                    else:
                        st.warning("⚠️ Username and password are required")
        
        # List existing users
        st.subheader("📋 Existing Users")
        
        users_data = []
        for username, user in self.users.items():
            users_data.append({
                'Username': username,
                'Full Name': user.full_name,
                'Role': user.role,
                'Email': user.email,
                'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                'Login Count': user.login_count,
                'Status': 'Active' if user.is_active else 'Inactive'
            })
        
        if users_data:
            users_df = pd.DataFrame(users_data)
            st.dataframe(users_df, use_container_width=True)
        
        # Role permissions info
        with st.expander("🔐 Role Permissions", expanded=False):
            for role, info in self.ROLES.items():
                st.markdown(f"**{role.title()}:** {info['description']}")
                st.markdown(f"Permissions: {', '.join(info['permissions'])}")
                st.markdown("---")

def require_role(required_role: str):
    """Decorator to require specific role for function access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = AuthManager()
            
            if not auth.is_authenticated():
                st.error("❌ Authentication required")
                auth.show_login()
                return None
            
            user = auth.get_current_user()
            if user.role != required_role and user.role != 'admin':
                st.error(f"❌ Access denied. {required_role.title()} role required.")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to require specific permission for function access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = AuthManager()
            
            if not auth.has_permission(required_permission):
                st.error(f"❌ Access denied. '{required_permission}' permission required.")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Activity logging
class ActivityLogger:
    """Log user activities for audit trail"""
    
    def __init__(self, log_file: str = "activity_log.json"):
        self.log_file = log_file
    
    def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log user activity"""
        current_user = st.session_state.get('username', 'anonymous')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': current_user,
            'activity_type': activity_type,
            'details': details,
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        
        try:
            # Load existing logs
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 10000 entries
            logs = logs[-10000:]
            
            # Save logs
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            st.error(f"Error logging activity: {e}")

# Usage example
if __name__ == "__main__":
    # Example usage in Streamlit app
    auth = AuthManager()
    
    if not auth.is_authenticated():
        auth.show_login()
    else:
        user = auth.get_current_user()
        st.success(f"Welcome, {user.full_name}!")
        
        # Show different content based on role
        if user.role == 'admin':
            auth.show_user_management()
        elif user.role == 'technician':
            st.info("Technician dashboard would go here")
        else:
            st.info("Viewer dashboard would go here")
        
        if st.sidebar.button("Logout"):
            auth.logout()
            st.rerun()

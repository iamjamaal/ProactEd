"""
Authentication System Tests
==========================

Comprehensive test suite for the authentication and authorization system.
Tests include user management, password security, session handling, and role-based access control.
"""

import pytest
import tempfile
import os
import sys
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import User, AuthManager


class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager for password testing"""
        return AuthManager()
    
    def test_password_hashing(self, auth_manager):
        """Test password hashing functionality"""
        password = "test_password_123"
        hashed = auth_manager._hash_password(password)
        
        # Verify hash is generated
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Hash should not equal plain text
        
        # Verify hash contains salt and hash components
        assert ':' in hashed
        salt, _ = hashed.split(':')
        assert len(salt) == 32  # 16 bytes = 32 hex chars
    
    def test_password_verification(self, auth_manager):
        """Test password verification"""
        password = "secure_password_456"
        hashed = auth_manager._hash_password(password)
        
        # Correct password should verify
        assert auth_manager._verify_password(password, hashed) == True
        
        # Incorrect password should not verify
        assert auth_manager._verify_password("wrong_password", hashed) == False
        assert auth_manager._verify_password("", hashed) == False
    
    def test_password_salt_uniqueness(self, auth_manager):
        """Test that password salts are unique"""
        password = "same_password"
        hash1 = auth_manager._hash_password(password)
        hash2 = auth_manager._hash_password(password)
        
        # Same password should produce different hashes due to unique salts
        assert hash1 != hash2
        
        # Both should still verify correctly
        assert auth_manager._verify_password(password, hash1) == True
        assert auth_manager._verify_password(password, hash2) == True


class TestUser:
    """Test User class functionality"""
    
    def test_user_creation(self):
        """Test user object creation"""
        user = User(
            username="testuser",
            password_hash="hashed_password",
            role="admin",
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "admin"
        assert user.full_name == "Test User"
        assert user.is_active == True
        assert user.created_at is not None
        assert user.last_login is None
    
    def test_user_to_dict(self):
        """Test user serialization"""
        user = User(
            username="testuser",
            password_hash="hashed_password",
            role="admin",
            email="test@example.com",
            full_name="Test User"
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == "admin"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["is_active"] == True
        assert "password_hash" in user_dict  # Password hash should be included in dict
    
    def test_user_from_dict(self):
        """Test user deserialization"""
        user_data = {
            "username": "dictuser",
            "password_hash": "hash123",
            "role": "technician",
            "email": "dict@example.com",
            "full_name": "Dict User",
            "is_active": True,
            "login_count": 5
        }
        
        user = User.from_dict(user_data)
        
        assert user.username == "dictuser"
        assert user.password_hash == "hash123"
        assert user.role == "technician"
        assert user.email == "dict@example.com"
        assert user.full_name == "Dict User"
        assert user.is_active == True
        assert user.login_count == 5


class TestAuthManager:
    """Test AuthManager functionality"""
    
    @pytest.fixture
    def temp_users_file(self):
        """Create temporary users file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def auth_manager(self, temp_users_file):
        """Create AuthManager instance with temporary file"""
        return AuthManager(users_file=temp_users_file)
    
    def test_auth_manager_initialization(self, auth_manager):
        """Test AuthManager initialization"""
        assert auth_manager.users_file is not None
        assert isinstance(auth_manager.users, pd.DataFrame)
        assert len(auth_manager.users) >= 1  # Should have default admin user
    
    def test_create_user(self, auth_manager):
        """Test user creation"""
        result = auth_manager.create_user(
            username="newuser",
            password="secure_password_123",
            role="technician",
            email="newuser@example.com",
            full_name="New User"
        )
        
        assert result == True
        
        # Verify user was created
        user = auth_manager.users.get("newuser")
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == "technician"
    
    def test_create_duplicate_user(self, auth_manager):
        """Test creating duplicate username"""
        # Create first user
        auth_manager.create_user(
            username="duplicate",
            password="password123",
            role="viewer",
            email="user1@example.com"
        )
        
        # Try to create user with same username
        result = auth_manager.create_user(
            username="duplicate",
            password="password456",
            role="admin",
            email="user2@example.com"
        )
        
        assert result == False  # Should fail due to duplicate username
    
    @patch('streamlit.session_state', {})
    def test_authenticate_user(self, auth_manager):
        """Test user authentication"""
        import streamlit as st
        
        # Create test user
        auth_manager.create_user(
            username="authtest",
            password="correct_password",
            role="technician",
            email="authtest@example.com"
        )
        
        # Test correct credentials
        result = auth_manager.authenticate("authtest", "correct_password")
        assert result == True
        assert st.session_state.get('authenticated') == True
        assert st.session_state.get('username') == "authtest"
        
        # Test incorrect password
        result = auth_manager.authenticate("authtest", "wrong_password")
        assert result == False
        
        # Test non-existent user
        result = auth_manager.authenticate("nonexistent", "any_password")
        assert result == False
    
    def test_update_user(self, auth_manager):
        """Test user update functionality"""
        # Create test user
        auth_manager.create_user(
            username="updatetest",
            password="password123",
            email="original@example.com",
            role="Viewer",
            full_name="Original Name"
        )
        
        # Update user
        result = auth_manager.update_user(
            username="updatetest",
            email="updated@example.com",
            role="Technician",
            full_name="Updated Name"
        )
        
        assert result == True
        
        # Verify updates
        user = auth_manager.get_user("updatetest")
        assert user.email == "updated@example.com"
        assert user.role == "Technician"
        assert user.full_name == "Updated Name"
    
    def test_delete_user(self, auth_manager):
        """Test user deletion"""
        # Create test user
        auth_manager.create_user(
            username="deletetest",
            password="password123",
            email="delete@example.com",
            role="Viewer"
        )
        
        # Verify user exists
        user = auth_manager.get_user("deletetest")
        assert user is not None
        
        # Delete user
        result = auth_manager.delete_user("deletetest")
        assert result == True
        
        # Verify user no longer exists
        user = auth_manager.get_user("deletetest")
        assert user is None
    
    def test_change_password(self, auth_manager):
        """Test password change functionality"""
        # Create test user
        auth_manager.create_user(
            username="passtest",
            password="old_password",
            email="passtest@example.com",
            role="Technician"
        )
        
        # Change password
        result = auth_manager.change_password("passtest", "old_password", "new_password")
        assert result == True
        
        # Test authentication with new password
        user = auth_manager.authenticate("passtest", "new_password")
        assert user is not None
        
        # Test that old password no longer works
        user = auth_manager.authenticate("passtest", "old_password")
        assert user is None
    
    def test_get_all_users(self, auth_manager):
        """Test getting all users"""
        # Create multiple test users
        auth_manager.create_user("user1", "pass1", "user1@test.com", "Admin")
        auth_manager.create_user("user2", "pass2", "user2@test.com", "Technician")
        auth_manager.create_user("user3", "pass3", "user3@test.com", "Viewer")
        
        users = auth_manager.get_all_users()
        
        # Should have at least the test users plus default admin
        assert len(users) >= 3
        
        # Check that all users are User objects
        for user in users:
            assert isinstance(user, User)
            assert hasattr(user, 'username')
            assert hasattr(user, 'role')


class TestSessionManagement:
    """Test session management functionality"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager for session testing"""
        return AuthManager()
    
    @patch('streamlit.session_state', {})
    def test_session_initialization(self, auth_manager):
        """Test session state initialization"""
        import streamlit as st
        
        auth_manager.initialize_session()
        
        assert hasattr(st.session_state, 'authenticated')
        assert hasattr(st.session_state, 'user')
        assert hasattr(st.session_state, 'login_time')
        assert st.session_state.authenticated == False
        assert st.session_state.user is None
    
    @patch('streamlit.session_state', {})
    def test_login_session(self, auth_manager):
        """Test session login"""
        import streamlit as st
        
        # Create test user
        auth_manager.create_user(
            username="sessiontest",
            password="password123",
            email="session@test.com",
            role="Technician"
        )
        
        # Initialize session
        auth_manager.initialize_session()
        
        # Login
        result = auth_manager.login("sessiontest", "password123")
        assert result == True
        
        # Check session state
        assert st.session_state.authenticated == True
        assert st.session_state.user is not None
        assert st.session_state.user.username == "sessiontest"
        assert st.session_state.login_time is not None
    
    @patch('streamlit.session_state', {})
    def test_logout_session(self, auth_manager):
        """Test session logout"""
        import streamlit as st
        
        # Initialize and login
        auth_manager.initialize_session()
        auth_manager.create_user("logouttest", "pass123", "logout@test.com", "Viewer")
        auth_manager.login("logouttest", "pass123")
        
        # Verify logged in
        assert st.session_state.authenticated == True
        
        # Logout
        auth_manager.logout()
        
        # Verify logged out
        assert st.session_state.authenticated == False
        assert st.session_state.user is None
        assert st.session_state.login_time is None


class TestActivityLogging:
    """Test activity logging functionality"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager for logging testing"""
        return AuthManager()
    
    def test_log_activity(self, auth_manager):
        """Test activity logging"""
        # Create test user
        auth_manager.create_user("logtest", "pass123", "log@test.com", "Admin")
        user = auth_manager.get_user("logtest")
        
        # Log an activity
        auth_manager.log_activity(user, "test_action", "Test activity description")
        
        # Verify activity was logged
        activities = auth_manager.get_user_activities("logtest")
        assert len(activities) > 0
        
        latest_activity = activities.iloc[-1]
        assert latest_activity['action'] == "test_action"
        assert latest_activity['description'] == "Test activity description"
        assert latest_activity['username'] == "logtest"
    
    def test_get_recent_activities(self, auth_manager):
        """Test getting recent activities"""
        # Create test user and log multiple activities
        auth_manager.create_user("activitytest", "pass123", "activity@test.com", "Technician")
        user = auth_manager.get_user("activitytest")
        
        auth_manager.log_activity(user, "login", "User logged in")
        auth_manager.log_activity(user, "view_dashboard", "Viewed main dashboard")
        auth_manager.log_activity(user, "update_equipment", "Updated equipment EQ-001")
        
        # Get recent activities
        recent_activities = auth_manager.get_recent_activities(limit=2)
        assert len(recent_activities) <= 2
        
        # Should be sorted by timestamp (most recent first)
        if len(recent_activities) > 1:
            assert recent_activities.iloc[0]['timestamp'] >= recent_activities.iloc[1]['timestamp']


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager with test users of different roles"""
        auth_manager = AuthManager()
        
        # Create users with different roles
        auth_manager.create_user("admin_user", "pass123", "admin", "admin@test.com", "Admin User")
        auth_manager.create_user("tech_user", "pass123", "technician", "tech@test.com", "Tech User")
        auth_manager.create_user("super_user", "pass123", "supervisor", "super@test.com", "Super User")
        auth_manager.create_user("view_user", "pass123", "viewer", "view@test.com", "View User")
        
        return auth_manager
    
    @patch('streamlit.session_state', {})
    def test_admin_permissions(self, auth_manager):
        """Test admin user permissions"""
        import streamlit as st
        
        # Login as admin
        auth_manager.initialize_session()
        auth_manager.login("admin_user", "pass123")
        
        # Admin should have system permissions
        assert auth_manager.has_permission("view_all") == True
        assert auth_manager.has_permission("edit_all") == True
        assert auth_manager.has_permission("manage_users") == True
        assert auth_manager.has_permission("system_config") == True
    
    @patch('streamlit.session_state', {})
    def test_technician_permissions(self, auth_manager):
        """Test technician user permissions"""
        import streamlit as st
        
        # Login as technician
        auth_manager.initialize_session()
        auth_manager.login("tech_user", "pass123")
        
        # Technician should have operational permissions but not administrative
        assert auth_manager.has_permission("view_equipment") == True
        assert auth_manager.has_permission("update_maintenance") == True
        assert auth_manager.has_permission("view_assignments") == True
        assert auth_manager.has_permission("manage_users") == False
        assert auth_manager.has_permission("system_config") == False
    
    @patch('streamlit.session_state', {})
    def test_supervisor_permissions(self, auth_manager):
        """Test supervisor user permissions"""
        import streamlit as st
        
        # Login as supervisor
        auth_manager.initialize_session()
        auth_manager.login("super_user", "pass123")
        
        # Supervisor should have management permissions
        assert auth_manager.has_permission("view_all") == True
        assert auth_manager.has_permission("assign_technicians") == True
        assert auth_manager.has_permission("approve_maintenance") == True
        assert auth_manager.has_permission("manage_users") == False
        assert auth_manager.has_permission("system_config") == False
    
    @patch('streamlit.session_state', {})
    def test_no_permissions_when_not_logged_in(self, auth_manager):
        """Test that no permissions are granted when not logged in"""
        import streamlit as st
        
        # Initialize session but don't login
        auth_manager.initialize_session()
        
        # Should have no permissions
        assert auth_manager.has_permission("view_all") == False
        assert auth_manager.has_permission("manage_users") == False
        assert auth_manager.has_permission("view_equipment") == False


class TestSecurityFeatures:
    """Test security features and edge cases"""
    
    @pytest.fixture
    def auth_manager(self):
        return AuthManager()
    
    def test_inactive_user_authentication(self, auth_manager):
        """Test that inactive users cannot authenticate"""
        # Create user and then deactivate
        auth_manager.create_user("inactive_user", "pass123", "inactive@test.com", "Viewer")
        auth_manager.update_user("inactive_user", is_active=False)
        
        # Should not be able to authenticate
        user = auth_manager.authenticate("inactive_user", "pass123")
        assert user is None
    
    def test_empty_password_handling(self, auth_manager):
        """Test handling of empty passwords"""
        # Should not be able to create user with empty password
        result = auth_manager.create_user("emptypass", "", "empty@test.com", "Viewer")
        assert result == False
    
    def test_invalid_role_handling(self, auth_manager):
        """Test handling of invalid roles"""
        # Should not be able to create user with invalid role
        result = auth_manager.create_user("invalidrole", "pass123", "invalid@test.com", "InvalidRole")
        assert result == False
    
    def test_special_characters_in_username(self, auth_manager):
        """Test username validation with special characters"""
        # Test various username formats
        valid_usernames = ["user123", "user_name", "user-name", "user.name"]
        invalid_usernames = ["user@name", "user name", "user#name", ""]
        
        for username in valid_usernames:
            result = auth_manager.create_user(username, "pass123", f"{username}@test.com", "Viewer")
            assert result == True, f"Valid username {username} should be accepted"
        
        for username in invalid_usernames:
            result = auth_manager.create_user(username, "pass123", f"test@test.com", "Viewer")
            assert result == False, f"Invalid username {username} should be rejected"


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.fixture
    def auth_manager(self):
        return AuthManager()
    
    def test_complete_user_lifecycle(self, auth_manager):
        """Test complete user lifecycle from creation to deletion"""
        # 1. Create user
        result = auth_manager.create_user(
            username="lifecycle_user",
            password="initial_password",
            email="lifecycle@test.com",
            role="Technician",
            full_name="Lifecycle Test User"
        )
        assert result == True
        
        # 2. Authenticate user
        user = auth_manager.authenticate("lifecycle_user", "initial_password")
        assert user is not None
        assert user.username == "lifecycle_user"
        
        # 3. Log some activities
        auth_manager.log_activity(user, "login", "Initial login")
        auth_manager.log_activity(user, "view_equipment", "Viewed equipment list")
        
        # 4. Change password
        result = auth_manager.change_password("lifecycle_user", "initial_password", "new_password")
        assert result == True
        
        # 5. Verify old password doesn't work
        user = auth_manager.authenticate("lifecycle_user", "initial_password")
        assert user is None
        
        # 6. Verify new password works
        user = auth_manager.authenticate("lifecycle_user", "new_password")
        assert user is not None
        
        # 7. Update user details
        result = auth_manager.update_user(
            username="lifecycle_user",
            email="new_email@test.com",
            role="Supervisor",
            full_name="Updated User Name"
        )
        assert result == True
        
        # 8. Verify updates
        user = auth_manager.get_user("lifecycle_user")
        assert user.email == "new_email@test.com"
        assert user.role == "Supervisor"
        assert user.full_name == "Updated User Name"
        
        # 9. Check activity history
        activities = auth_manager.get_user_activities("lifecycle_user")
        assert len(activities) >= 2
        
        # 10. Delete user
        result = auth_manager.delete_user("lifecycle_user")
        assert result == True
        
        # 11. Verify user is gone
        user = auth_manager.get_user("lifecycle_user")
        assert user is None
    
    @patch('streamlit.session_state', {})
    def test_session_timeout_scenario(self, auth_manager):
        """Test session timeout functionality"""
        import streamlit as st
        from datetime import datetime, timedelta
        
        # Initialize session and login
        auth_manager.initialize_session()
        auth_manager.create_user("timeout_user", "pass123", "timeout@test.com", "Viewer")
        auth_manager.login("timeout_user", "pass123")
        
        # Verify logged in
        assert st.session_state.authenticated == True
        
        # Simulate session timeout by manually setting old login time
        old_time = datetime.now() - timedelta(hours=9)  # 9 hours ago (timeout is 8 hours)
        st.session_state.login_time = old_time
        
        # Check if session is expired
        is_expired = auth_manager.is_session_expired()
        assert is_expired == True
        
        # Session should be automatically logged out
        if is_expired:
            auth_manager.logout()
        
        assert st.session_state.authenticated == False


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

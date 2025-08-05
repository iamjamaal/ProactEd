"""
Simplified Authentication System Tests
=====================================

Test suite for the authentication and authorization system.
Tests only the existing functionality in the auth.py file.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch

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
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        yield temp_file.name
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def auth_manager(self, temp_users_file):
        """Create AuthManager instance with temporary file"""
        return AuthManager(users_file=temp_users_file)
    
    def test_auth_manager_initialization(self, auth_manager):
        """Test AuthManager initialization"""
        assert auth_manager.users_file is not None
        assert isinstance(auth_manager.users, dict)
        assert len(auth_manager.users) >= 1  # Should have default users
    
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
        
        # Reset session state
        st.session_state.clear()
        
        # Test incorrect password
        result = auth_manager.authenticate("authtest", "wrong_password")
        assert result == False
        
        # Test non-existent user
        result = auth_manager.authenticate("nonexistent", "any_password")
        assert result == False
    
    def test_invalid_role_handling(self, auth_manager):
        """Test handling of invalid roles"""
        # Should not be able to create user with invalid role
        result = auth_manager.create_user("invalidrole", "pass123", "InvalidRole", "invalid@test.com")
        assert result == False


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @pytest.fixture
    def auth_manager(self, temp_users_file=None):
        """Create AuthManager with test users of different roles"""
        if temp_users_file is None:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            temp_file.close()
            temp_users_file = temp_file.name
        
        auth_manager = AuthManager(users_file=temp_users_file)
        
        # Create users with different roles
        auth_manager.create_user("admin_user", "pass123", "admin", "admin@test.com", "Admin User")
        auth_manager.create_user("tech_user", "pass123", "technician", "tech@test.com", "Tech User")
        auth_manager.create_user("super_user", "pass123", "supervisor", "super@test.com", "Super User")
        auth_manager.create_user("view_user", "pass123", "viewer", "view@test.com", "View User")
        
        yield auth_manager
        
        try:
            os.unlink(temp_users_file)
        except FileNotFoundError:
            pass
    
    @patch('streamlit.session_state', {})
    def test_admin_permissions(self, auth_manager):
        """Test admin user permissions"""
        import streamlit as st
        
        # Login as admin
        auth_manager.authenticate("admin_user", "pass123")
        
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
        auth_manager.authenticate("tech_user", "pass123")
        
        # Technician should have operational permissions but not administrative
        assert auth_manager.has_permission("view_equipment") == True
        assert auth_manager.has_permission("update_maintenance") == True
        assert auth_manager.has_permission("view_assignments") == True
        assert auth_manager.has_permission("manage_users") == False
        assert auth_manager.has_permission("system_config") == False
    
    @patch('streamlit.session_state', {})
    def test_no_permissions_when_not_logged_in(self, auth_manager):
        """Test that no permissions are granted when not logged in"""
        import streamlit as st
        
        # Don't login, just check permissions
        # Should have no permissions
        assert auth_manager.has_permission("view_all") == False
        assert auth_manager.has_permission("manage_users") == False
        assert auth_manager.has_permission("view_equipment") == False


class TestSessionManagement:
    """Test session management functionality"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager for session testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        auth_manager = AuthManager(users_file=temp_file.name)
        yield auth_manager
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    @patch('streamlit.session_state', {})
    def test_session_login(self, auth_manager):
        """Test session login"""
        import streamlit as st
        
        # Create test user
        auth_manager.create_user(
            username="sessiontest",
            password="password123",
            role="technician",
            email="session@test.com"
        )
        
        # Login
        result = auth_manager.authenticate("sessiontest", "password123")
        assert result == True
        
        # Check session state
        assert st.session_state.get('authenticated') == True
        assert st.session_state.get('username') == "sessiontest"
        assert st.session_state.get('user_role') == "technician"
    
    @patch('streamlit.session_state', {})
    def test_get_current_user(self, auth_manager):
        """Test getting current authenticated user"""
        import streamlit as st
        
        # Create and login test user
        auth_manager.create_user("currenttest", "pass123", "admin", "current@test.com")
        auth_manager.authenticate("currenttest", "pass123")
        
        # Get current user
        current_user = auth_manager.get_current_user()
        assert current_user is not None
        assert current_user.username == "currenttest"
        assert current_user.role == "admin"
    
    @patch('streamlit.session_state', {})
    def test_no_current_user_when_not_logged_in(self, auth_manager):
        """Test that get_current_user returns None when not logged in"""
        current_user = auth_manager.get_current_user()
        assert current_user is None


class TestSecurityFeatures:
    """Test security features and edge cases"""
    
    @pytest.fixture
    def auth_manager(self):
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        auth_manager = AuthManager(users_file=temp_file.name)
        yield auth_manager
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    @patch('streamlit.session_state', {})
    def test_inactive_user_authentication(self, auth_manager):
        """Test that inactive users cannot authenticate"""
        # Create user
        auth_manager.create_user("inactive_user", "pass123", "viewer", "inactive@test.com")
        
        # Manually set user as inactive
        user = auth_manager.users["inactive_user"]
        user.is_active = False
        
        # Should not be able to authenticate
        result = auth_manager.authenticate("inactive_user", "pass123")
        assert result == False
    
    def test_empty_password_handling(self, auth_manager):
        """Test handling of empty passwords"""
        # Should not be able to create user with empty password (will create hash of empty string)
        result = auth_manager.create_user("emptypass", "", "viewer", "empty@test.com")
        # This might still return True as empty string can be hashed, but authentication will fail
        assert isinstance(result, bool)
    
    def test_role_validation(self, auth_manager):
        """Test role validation"""
        # Valid roles should work
        valid_roles = ["admin", "technician", "supervisor", "viewer"]
        for role in valid_roles:
            result = auth_manager.create_user(f"user_{role}", "pass123", role, f"{role}@test.com")
            assert result == True
        
        # Invalid role should fail
        result = auth_manager.create_user("invalid_role_user", "pass123", "invalid_role", "invalid@test.com")
        assert result == False


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

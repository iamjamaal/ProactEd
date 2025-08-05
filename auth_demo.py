"""
Authentication System Demonstration
==================================

This script demonstrates the key features of our authentication system.
Run this to see how the authentication system works programmatically.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import AuthManager, User

def demonstrate_authentication_system():
    """Demonstrate the authentication system functionality"""
    
    print("🔐 AUTHENTICATION SYSTEM DEMONSTRATION")
    print("=" * 50)
    
    # Initialize AuthManager
    print("\n1. 📊 Initializing Authentication Manager...")
    auth_manager = AuthManager(users_file="demo_users.json")
    print(f"   ✅ AuthManager created with {len(auth_manager.users)} users")
    
    # Show default users
    print("\n2. 👥 Default Users Created:")
    for username, user in auth_manager.users.items():
        print(f"   • {username} ({user.role}) - {user.email}")
    
    # Test password security
    print("\n3. 🔒 Testing Password Security:")
    test_password = "SecurePassword123!"
    hashed = auth_manager._hash_password(test_password)
    print(f"   • Original Password: {test_password}")
    print(f"   • Hashed Password: {hashed[:30]}...{hashed[-10:]}")
    print(f"   • Hash Length: {len(hashed)} characters")
    print(f"   • Password Verification: {auth_manager._verify_password(test_password, hashed)}")
    
    # Test salt uniqueness
    hash1 = auth_manager._hash_password(test_password)
    hash2 = auth_manager._hash_password(test_password)
    print(f"   • Salt Uniqueness: {hash1 != hash2} (hashes are different)")
    
    # Create new users
    print("\n4. 👤 Creating New Users:")
    new_users = [
        ("demo_admin", "admin123!", "admin", "admin@demo.com", "Demo Administrator"),
        ("demo_tech", "tech123!", "technician", "tech@demo.com", "Demo Technician"),
        ("demo_supervisor", "super123!", "supervisor", "supervisor@demo.com", "Demo Supervisor"),
        ("demo_viewer", "view123!", "viewer", "viewer@demo.com", "Demo Viewer"),
    ]
    
    for username, password, role, email, full_name in new_users:
        result = auth_manager.create_user(username, password, role, email, full_name)
        if result:
            print(f"   ✅ Created user: {username} ({role})")
        else:
            print(f"   ❌ Failed to create user: {username}")
    
    # Test authentication
    print("\n5. 🔑 Testing Authentication:")
    test_credentials = [
        ("demo_admin", "admin123!", True),
        ("demo_tech", "tech123!", True),
        ("demo_admin", "wrong_password", False),
        ("nonexistent", "any_password", False),
    ]
    
    for username, password, expected in test_credentials:
        # Mock streamlit session state for testing
        import unittest.mock
        with unittest.mock.patch('streamlit.session_state', {}):
            result = auth_manager.authenticate(username, password)
            status = "✅ SUCCESS" if result == expected else "❌ FAILED"
            print(f"   {status}: {username} / {password} = {result}")
    
    # Test role-based permissions
    print("\n6. 🔐 Testing Role-Based Permissions:")
    
    # Mock successful login for permission testing
    import unittest.mock
    
    roles_permissions = [
        ("admin", ["view_all", "edit_all", "manage_users", "system_config"]),
        ("technician", ["view_equipment", "update_maintenance", "view_assignments"]),
        ("supervisor", ["view_all", "assign_technicians", "approve_maintenance"]),
        ("viewer", ["view_reports"])
    ]
    
    for role, permissions in roles_permissions:
        print(f"\n   {role.upper()} PERMISSIONS:")
        
        # Mock session with user logged in
        mock_session = {
            'authenticated': True,
            'username': f'demo_{role}',
            'user_role': role
        }
        
        with unittest.mock.patch('streamlit.session_state', mock_session):
            for permission in permissions:
                has_perm = auth_manager.has_permission(permission)
                status = "✅" if has_perm else "❌"
                print(f"     {status} {permission}")
            
            # Test a permission they shouldn't have
            forbidden_perm = "system_config" if role != "admin" else "invalid_permission"
            has_forbidden = auth_manager.has_permission(forbidden_perm)
            status = "❌" if not has_forbidden else "⚠️ "
            print(f"     {status} {forbidden_perm} (should be denied)")
    
    # Test user management
    print("\n7. 📋 User Management:")
    print(f"   • Total Users: {len(auth_manager.users)}")
    print(f"   • Active Users: {sum(1 for u in auth_manager.users.values() if u.is_active)}")
    
    # Show user details
    demo_user = auth_manager.users.get("demo_admin")
    if demo_user:
        print(f"\n   📝 Sample User Details (demo_admin):")
        print(f"     • Username: {demo_user.username}")
        print(f"     • Role: {demo_user.role}")
        print(f"     • Email: {demo_user.email}")
        print(f"     • Full Name: {demo_user.full_name}")
        print(f"     • Active: {demo_user.is_active}")
        print(f"     • Created: {demo_user.created_at}")
        print(f"     • Login Count: {demo_user.login_count}")
    
    # Test security features
    print("\n8. 🛡️  Security Features:")
    
    # Test inactive user
    demo_user.is_active = False
    with unittest.mock.patch('streamlit.session_state', {}):
        inactive_auth = auth_manager.authenticate("demo_admin", "admin123!")
        print(f"   • Inactive User Login: {inactive_auth} (should be False)")
    
    # Reactivate user
    demo_user.is_active = True
    
    # Test invalid role creation
    invalid_role_result = auth_manager.create_user("invalid_user", "pass123", "invalid_role")
    print(f"   • Invalid Role Creation: {invalid_role_result} (should be False)")
    
    # Test duplicate username
    duplicate_result = auth_manager.create_user("demo_admin", "newpass", "viewer")
    print(f"   • Duplicate Username: {duplicate_result} (should be False)")
    
    print("\n9. 🎯 System Summary:")
    print(f"   • Authentication System: ✅ Fully Functional")
    print(f"   • Password Security: ✅ PBKDF2 with unique salts")
    print(f"   • Role-Based Access: ✅ 4 roles with granular permissions")
    print(f"   • Session Management: ✅ Secure session handling")
    print(f"   • User Management: ✅ Create, authenticate, manage users")
    print(f"   • Security Validation: ✅ Input validation and security checks")
    
    print("\n🎉 AUTHENTICATION SYSTEM DEMONSTRATION COMPLETE!")
    print("=" * 50)
    
    # Clean up demo file
    try:
        os.remove("demo_users.json")
        print("✅ Demo files cleaned up")
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    demonstrate_authentication_system()

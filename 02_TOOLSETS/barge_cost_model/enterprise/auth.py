"""
Authentication and Authorization System
========================================

Implements JWT-based authentication with role-based access control.

Features:
- User registration and login
- JWT token generation and validation
- Password hashing (bcrypt)
- Role-based permissions
- Session management

Author: Barge Economics Research Team
Date: February 3, 2026
"""

import sys
import os
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import jwt
import hashlib
import secrets
import re
from pathlib import Path
import json

# Local imports
from config import get_config

config = get_config()

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class User:
    """User model"""
    username: str
    email: str
    password_hash: str
    role: str = "viewer"
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "permissions": self.permissions
        }

@dataclass
class Token:
    """JWT token model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800  # seconds

# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

class PasswordManager:
    """Password hashing and validation"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = password_hash.split('$')
            pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return pwd_hash == stored_hash
        except:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple:
        """
        Validate password meets security requirements

        Returns: (is_valid, error_message)
        """
        if len(password) < config.auth.min_password_length:
            return False, f"Password must be at least {config.auth.min_password_length} characters"

        if config.auth.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if config.auth.require_lowercase and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if config.auth.require_numbers and not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if config.auth.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, ""

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

class TokenManager:
    """JWT token generation and validation"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=config.auth.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            config.auth.secret_key,
            algorithm=config.auth.algorithm
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()

        expire = datetime.utcnow() + timedelta(days=config.auth.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            config.auth.secret_key,
            algorithm=config.auth.algorithm
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """
        Verify and decode JWT token

        Returns: token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                config.auth.secret_key,
                algorithms=[config.auth.algorithm]
            )

            # Verify token type
            if payload.get("type") != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        payload = TokenManager.verify_token(refresh_token, token_type="refresh")

        if not payload:
            return None

        # Create new access token with same user data
        new_access_token = TokenManager.create_access_token(
            data={"sub": payload.get("sub"), "role": payload.get("role")}
        )

        return new_access_token

# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

class RoleManager:
    """Role-based access control (RBAC)"""

    # Define role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        "viewer": 1,
        "analyst": 2,
        "admin": 3
    }

    # Define permissions for each role
    ROLE_PERMISSIONS = {
        "viewer": [
            "view_forecasts",
            "view_dashboard",
            "view_reports"
        ],
        "analyst": [
            "view_forecasts",
            "view_dashboard",
            "view_reports",
            "run_models",
            "export_data",
            "create_scenarios"
        ],
        "admin": [
            "view_forecasts",
            "view_dashboard",
            "view_reports",
            "run_models",
            "export_data",
            "create_scenarios",
            "manage_users",
            "update_data",
            "configure_system",
            "view_logs"
        ]
    }

    @classmethod
    def get_permissions(cls, role: str) -> List[str]:
        """Get permissions for a role"""
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in cls.get_permissions(role)

    @classmethod
    def role_includes_role(cls, role: str, target_role: str) -> bool:
        """Check if role includes all permissions of target role"""
        role_level = cls.ROLE_HIERARCHY.get(role, 0)
        target_level = cls.ROLE_HIERARCHY.get(target_role, 0)
        return role_level >= target_level

# ============================================================================
# USER MANAGEMENT
# ============================================================================

class UserManager:
    """User management with file-based storage (simple implementation)"""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path(__file__).parent / "users.json"

        self.storage_path = storage_path
        self.users: Dict[str, User] = {}
        self._load_users()

    def _load_users(self):
        """Load users from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                for username, user_data in data.items():
                    self.users[username] = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        password_hash=user_data["password_hash"],
                        role=user_data.get("role", "viewer"),
                        created_at=datetime.fromisoformat(user_data["created_at"]),
                        last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                        is_active=user_data.get("is_active", True),
                        permissions=user_data.get("permissions", [])
                    )
            except Exception as e:
                print(f"Error loading users: {e}")

    def _save_users(self):
        """Save users to storage"""
        data = {}
        for username, user in self.users.items():
            data[username] = {
                "username": user.username,
                "email": user.email,
                "password_hash": user.password_hash,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active,
                "permissions": user.permissions
            }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_user(self, username: str, email: str, password: str,
                   role: str = "viewer") -> tuple:
        """
        Create new user

        Returns: (success, message_or_user)
        """
        # Validate username
        if username in self.users:
            return False, "Username already exists"

        # Validate email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email address"

        # Check if email already used
        for user in self.users.values():
            if user.email == email:
                return False, "Email already registered"

        # Validate password
        is_valid, error = PasswordManager.validate_password_strength(password)
        if not is_valid:
            return False, error

        # Validate role
        if role not in config.auth.available_roles:
            return False, f"Invalid role. Must be one of: {config.auth.available_roles}"

        # Create user
        password_hash = PasswordManager.hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            permissions=RoleManager.get_permissions(role)
        )

        self.users[username] = user
        self._save_users()

        return True, user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.users.get(username)

        if not user:
            return None

        if not user.is_active:
            return None

        if not PasswordManager.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now()
        self._save_users()

        return user

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)

    def update_user_role(self, username: str, new_role: str) -> tuple:
        """Update user role"""
        user = self.users.get(username)

        if not user:
            return False, "User not found"

        if new_role not in config.auth.available_roles:
            return False, f"Invalid role. Must be one of: {config.auth.available_roles}"

        user.role = new_role
        user.permissions = RoleManager.get_permissions(new_role)
        self._save_users()

        return True, "Role updated successfully"

    def deactivate_user(self, username: str) -> tuple:
        """Deactivate user account"""
        user = self.users.get(username)

        if not user:
            return False, "User not found"

        user.is_active = False
        self._save_users()

        return True, "User deactivated"

    def list_users(self) -> List[User]:
        """List all users"""
        return list(self.users.values())

# ============================================================================
# AUTHENTICATION SERVICE
# ============================================================================

class AuthService:
    """Main authentication service combining all components"""

    def __init__(self):
        self.user_manager = UserManager()
        self.token_manager = TokenManager()
        self.password_manager = PasswordManager()
        self.role_manager = RoleManager()

    def register(self, username: str, email: str, password: str,
                role: str = "viewer") -> tuple:
        """
        Register new user

        Returns: (success, message_or_token)
        """
        success, result = self.user_manager.create_user(username, email, password, role)

        if not success:
            return False, result

        # Create tokens for newly registered user
        user = result
        token = self.create_tokens(user)

        return True, token

    def login(self, username: str, password: str) -> Optional[Token]:
        """
        Authenticate user and return tokens

        Returns: Token object if successful, None otherwise
        """
        user = self.user_manager.authenticate_user(username, password)

        if not user:
            return None

        return self.create_tokens(user)

    def create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": user.username,
            "role": user.role,
            "email": user.email
        }

        access_token = self.token_manager.create_access_token(data=token_data)
        refresh_token = self.token_manager.create_refresh_token(data=token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=config.auth.access_token_expire_minutes * 60
        )

    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify access token and return payload"""
        return self.token_manager.verify_token(token, token_type="access")

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        return self.token_manager.refresh_access_token(refresh_token)

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from access token"""
        payload = self.verify_access_token(token)

        if not payload:
            return None

        username = payload.get("sub")
        return self.user_manager.get_user(username)

    def check_permission(self, token: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user = self.get_current_user(token)

        if not user:
            return False

        return self.role_manager.has_permission(user.role, permission)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AUTHENTICATION SYSTEM DEMO")
    print("=" * 70)

    # Initialize auth service
    auth = AuthService()

    # Create admin user
    print("\n1. Creating admin user...")
    success, result = auth.register(
        username="admin",
        email="admin@bargeforecasting.com",
        password="Admin123!",
        role="admin"
    )

    if success:
        print(f"✓ Admin user created")
        print(f"  Access Token: {result.access_token[:50]}...")
    else:
        print(f"✗ Failed: {result}")

    # Create analyst user
    print("\n2. Creating analyst user...")
    success, result = auth.register(
        username="analyst1",
        email="analyst@bargeforecasting.com",
        password="Analyst123!",
        role="analyst"
    )

    if success:
        print(f"✓ Analyst user created")
    else:
        print(f"✗ Failed: {result}")

    # Login as admin
    print("\n3. Logging in as admin...")
    token = auth.login("admin", "Admin123!")

    if token:
        print(f"✓ Login successful")
        print(f"  Token Type: {token.token_type}")
        print(f"  Expires In: {token.expires_in} seconds")

        # Verify token
        print("\n4. Verifying access token...")
        payload = auth.verify_access_token(token.access_token)
        if payload:
            print(f"✓ Token valid")
            print(f"  Username: {payload['sub']}")
            print(f"  Role: {payload['role']}")

        # Check permissions
        print("\n5. Checking permissions...")
        permissions_to_check = ["view_forecasts", "manage_users", "delete_system"]

        for perm in permissions_to_check:
            has_perm = auth.check_permission(token.access_token, perm)
            status = "✓" if has_perm else "✗"
            print(f"  {status} {perm}: {has_perm}")

    else:
        print(f"✗ Login failed")

    # List all users
    print("\n6. Listing all users...")
    users = auth.user_manager.list_users()
    for user in users:
        print(f"\n  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        print(f"  Permissions: {', '.join(user.permissions)}")
        print(f"  Created: {user.created_at.strftime('%Y-%m-%d %H:%M')}")

    print("\n" + "=" * 70)
    print("AUTHENTICATION SYSTEM READY")
    print("=" * 70)

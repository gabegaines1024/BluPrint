"""Authentication service for user management and JWT token handling."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from app.database import db
from app.models import User
from app.exceptions import ValidationError, NotFoundError, AuthenticationError


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            username: Unique username.
            email: Unique email address.
            password: Plain text password.
        
        Returns:
            Dictionary with user data and access token.
        
        Raises:
            ValidationError: If validation fails.
        """
        # Validate input
        if not username or len(username.strip()) < 3:
            raise ValidationError('Username must be at least 3 characters long')
        
        if not email or '@' not in email:
            raise ValidationError('Invalid email address')
        
        if not password or len(password) < 6:
            raise ValidationError('Password must be at least 6 characters long')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            raise ValidationError('Username already exists')
        
        if User.query.filter_by(email=email).first():
            raise ValidationError('Email already registered')
        
        # Create new user
        user = User(username=username.strip().lower(), email=email.strip().lower())
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return {
            'user': user.to_dict(),
            'access_token': access_token,
            'message': 'User registered successfully'
        }
    
    @staticmethod
    def login_user(username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return access token.
        
        Args:
            username: Username or email.
            password: Plain text password.
        
        Returns:
            Dictionary with user data and access token.
        
        Raises:
            AuthenticationError: If authentication fails.
        """
        if not username or not password:
            raise AuthenticationError('Username and password are required')
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username.lower()) | (User.email == username.lower())
        ).first()
        
        if not user or not user.check_password(password):
            raise AuthenticationError('Invalid username or password')
        
        if not user.is_active:
            raise AuthenticationError('Account is inactive')
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return {
            'user': user.to_dict(),
            'access_token': access_token,
            'message': 'Login successful'
        }
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID.
        
        Returns:
            User object or None.
        """
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username.
        
        Returns:
            User object or None.
        """
        return User.query.filter_by(username=username.lower()).first()
    
    @staticmethod
    def update_user(user_id: int, **kwargs) -> User:
        """Update user information.
        
        Args:
            user_id: User ID.
            **kwargs: Fields to update.
        
        Returns:
            Updated user object.
        
        Raises:
            NotFoundError: If user not found.
            ValidationError: If validation fails.
        """
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('User not found')
        
        if 'email' in kwargs:
            email = kwargs['email'].strip().lower()
            if '@' not in email:
                raise ValidationError('Invalid email address')
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user_id:
                raise ValidationError('Email already in use')
            user.email = email
        
        if 'password' in kwargs:
            password = kwargs['password']
            if len(password) < 6:
                raise ValidationError('Password must be at least 6 characters long')
            user.set_password(password)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user


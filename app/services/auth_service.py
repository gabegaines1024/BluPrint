"""Authentication service for user management and JWT token handling."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import User
from app.dependencies import create_access_token
from app.exceptions import ValidationError, NotFoundError, AuthenticationError
from app.schemas import UserResponse


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def register_user(username: str, email: str, password: str, db: Session) -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            username: Unique username.
            email: Unique email address.
            password: Plain text password.
            db: Database session.
        
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
        if db.query(User).filter(User.username == username.lower()).first():
            raise ValidationError('Username already exists')
        
        if db.query(User).filter(User.email == email.lower()).first():
            raise ValidationError('Email already registered')
        
        # Create new user
        user = User(username=username.strip().lower(), email=email.strip().lower())
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Generate access token
        access_token = create_access_token({'sub': user.id})
        
        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'user': UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at
            )
        }
    
    @staticmethod
    def login_user(username: str, password: str, db: Session) -> Dict[str, Any]:
        """Authenticate a user and return access token.
        
        Args:
            username: Username or email.
            password: Plain text password.
            db: Database session.
        
        Returns:
            Dictionary with user data and access token.
        
        Raises:
            AuthenticationError: If authentication fails.
        """
        if not username or not password:
            raise AuthenticationError('Username and password are required')
        
        # Try to find user by username or email
        user = db.query(User).filter(
            or_(User.username == username.lower(), User.email == username.lower())
        ).first()
        
        if not user or not user.check_password(password):
            raise AuthenticationError('Invalid username or password')
        
        if not user.is_active:
            raise AuthenticationError('Account is inactive')
        
        # Generate access token
        access_token = create_access_token({'sub': user.id})
        
        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'user': UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at
            )
        }
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID.
            db: Database session.
        
        Returns:
            User object or None.
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(username: str, db: Session) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username.
            db: Database session.
        
        Returns:
            User object or None.
        """
        return db.query(User).filter(User.username == username.lower()).first()
    
    @staticmethod
    def update_user(user_id: int, db: Session, **kwargs) -> User:
        """Update user information.
        
        Args:
            user_id: User ID.
            db: Database session.
            **kwargs: Fields to update.
        
        Returns:
            Updated user object.
        
        Raises:
            NotFoundError: If user not found.
            ValidationError: If validation fails.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError('User not found')
        
        if 'email' in kwargs:
            email = kwargs['email'].strip().lower()
            if '@' not in email:
                raise ValidationError('Invalid email address')
            existing = db.query(User).filter(User.email == email).first()
            if existing and existing.id != user_id:
                raise ValidationError('Email already in use')
            user.email = email
        
        if 'password' in kwargs:
            password = kwargs['password']
            if len(password) < 6:
                raise ValidationError('Password must be at least 6 characters long')
            user.set_password(password)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user


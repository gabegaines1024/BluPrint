"""Authentication utilities and decorators."""

from functools import wraps
from typing import Callable, Any
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.services.auth_service import AuthService
from app.exceptions import AuthorizationError


def get_current_user_id() -> int:
    """Get the current authenticated user ID.
    
    Returns:
        User ID from JWT token.
    
    Raises:
        AuthorizationError: If user is not authenticated.
    """
    try:
        verify_jwt_in_request()
        return get_jwt_identity()
    except Exception:
        raise AuthorizationError('Authentication required')


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for a route.
    
    Args:
        f: Function to decorate.
    
    Returns:
        Decorated function.
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def require_ownership(resource_getter: Callable) -> Callable:
    """Decorator to require ownership of a resource.
    
    Args:
        resource_getter: Function that takes route args and returns resource object with user_id.
    
    Returns:
        Decorator function.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            resource = resource_getter(*args, **kwargs)
            
            if not resource:
                from app.exceptions import NotFoundError
                raise NotFoundError('Resource not found')
            
            if hasattr(resource, 'user_id') and resource.user_id != user_id:
                raise AuthorizationError('You do not have permission to access this resource')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


"""API routes for authentication."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.database import db
from app.services.auth_service import AuthService
from app.exceptions import ValidationError, AuthenticationError, NotFoundError
from app.models import User

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@bp.route('/register', methods=['POST'])
def register() -> Tuple[Dict[str, Any], int]:
    """Register a new user.
    
    Request Body:
        username: Unique username (required).
        email: Unique email address (required).
        password: Password (required, min 6 characters).
    
    Returns:
        JSON response with user data and access token.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        result = AuthService.register_user(username, email, password)
        
        logger.info(f'User registered: {username}')
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error registering user: {e}', exc_info=True)
        return jsonify({'error': 'Failed to register user'}), 500


@bp.route('/login', methods=['POST'])
def login() -> Tuple[Dict[str, Any], int]:
    """Authenticate a user and return access token.
    
    Request Body:
        username: Username or email (required).
        password: Password (required).
    
    Returns:
        JSON response with user data and access token.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        result = AuthService.login_user(username, password)
        
        logger.info(f'User logged in: {username}')
        return jsonify(result), 200
        
    except AuthenticationError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        logger.error(f'Error logging in user: {e}', exc_info=True)
        return jsonify({'error': 'Failed to authenticate user'}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user() -> Tuple[Dict[str, Any], int]:
    """Get current authenticated user information.
    
    Returns:
        JSON response with current user data.
    """
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f'Error getting current user: {e}', exc_info=True)
        return jsonify({'error': 'Failed to get user information'}), 500


@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user() -> Tuple[Dict[str, Any], int]:
    """Update current authenticated user information.
    
    Request Body:
        email: New email address (optional).
        password: New password (optional).
    
    Returns:
        JSON response with updated user data.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400
        
        user = AuthService.update_user(user_id, **data)
        
        logger.info(f'User updated: {user_id}')
        return jsonify({'user': user.to_dict(), 'message': 'User updated successfully'}), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message}), e.status_code
    except NotFoundError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating user: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update user'}), 500


"""API routes for PC Building Agent."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.database import db
from app.models import Build
from app.services.agent_service import PCBuildingAgent
from app.exceptions import ValidationError

bp = Blueprint('agent', __name__)
logger = logging.getLogger(__name__)

# Store conversation contexts per user (in production, use Redis or database)
_user_contexts: Dict[int, Dict[str, Any]] = {}


def get_agent() -> PCBuildingAgent:
    """Get or create agent instance."""
    return PCBuildingAgent()


@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat() -> Tuple[Dict[str, Any], int]:
    """Send a message to the agent and get a response.
    
    Request Body:
        message: User's message (required).
    
    Returns:
        JSON response with agent message, recommendations, and updated context.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or initialize user context
        context = _user_contexts.get(user_id)
        
        # Process message
        agent = get_agent()
        result = agent.process_message(message, user_id, context)
        
        # Update stored context
        _user_contexts[user_id] = result['updated_context']
        
        # Format response
        response = {
            'message': result['message'],
            'recommended_parts': result.get('recommended_parts', []),
            'build_suggestion': result.get('build_suggestion')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f'Error in agent chat: {e}', exc_info=True)
        return jsonify({'error': 'Failed to process message'}), 500


@bp.route('/context', methods=['GET'])
@jwt_required()
def get_context() -> Tuple[Dict[str, Any], int]:
    """Get current conversation context.
    
    Returns:
        JSON response with current conversation context.
    """
    try:
        user_id = get_jwt_identity()
        context = _user_contexts.get(user_id, {})
        
        return jsonify({'context': context}), 200
        
    except Exception as e:
        logger.error(f'Error getting context: {e}', exc_info=True)
        return jsonify({'error': 'Failed to get context'}), 500


@bp.route('/reset', methods=['POST'])
@jwt_required()
def reset() -> Tuple[Dict[str, Any], int]:
    """Reset the conversation context.
    
    Returns:
        JSON response confirming reset.
    """
    try:
        user_id = get_jwt_identity()
        _user_contexts[user_id] = {}
        
        return jsonify({'message': 'Conversation reset successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error resetting context: {e}', exc_info=True)
        return jsonify({'error': 'Failed to reset conversation'}), 500


@bp.route('/save-build', methods=['POST'])
@jwt_required()
def save_build() -> Tuple[Dict[str, Any], int]:
    """Save a build from the agent conversation.
    
    Request Body:
        name: Build name (required).
        parts: List of part IDs (required).
        description: Optional description.
    
    Returns:
        JSON response with saved build data.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        name = data.get('name', 'My PC Build').strip()
        part_ids = data.get('parts', [])
        description = data.get('description')
        
        if not part_ids:
            return jsonify({'error': 'At least one part is required'}), 400
        
        if not isinstance(part_ids, list):
            return jsonify({'error': 'parts must be an array'}), 400
        
        # Import here to avoid circular imports
        from app.services.compatibility_service import (
            check_build_compatibility,
            calculate_build_price
        )
        
        # Check compatibility
        compat_result = check_build_compatibility(part_ids)
        
        # Calculate price
        total_price = calculate_build_price(part_ids)
        
        # Create build
        build = Build(
            user_id=user_id,
            name=name,
            description=description,
            parts=part_ids,
            total_price=total_price,
            is_compatible=compat_result['is_compatible'],
            compatibility_issues=compat_result.get('issues', [])
        )
        
        db.session.add(build)
        db.session.commit()
        
        logger.info(f'Build saved from agent: {build.id} by user {user_id}')
        return jsonify(build.to_dict()), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error saving build from agent: {e}', exc_info=True)
        return jsonify({'error': 'Failed to save build'}), 500


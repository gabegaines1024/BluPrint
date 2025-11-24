"""API routes for compatibility checking and rules management."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.database import db
from app.models import CompatibilityRule, Part
from app.services.compatibility_service import check_build_compatibility
from app.exceptions import ValidationError, NotFoundError

bp = Blueprint('compatibility', __name__)
logger = logging.getLogger(__name__)


@bp.route('/check', methods=['POST'])
@jwt_required()
def check_compatibility() -> Tuple[Dict[str, Any], int]:
    """Check compatibility of a list of parts (must be owned by user)."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        part_ids = data.get('part_ids', [])
        
        if not isinstance(part_ids, list):
            return jsonify({'error': 'part_ids must be an array'}), 400
        
        if not part_ids:
            return jsonify({
                'is_compatible': True,
                'issues': [],
                'warnings': []
            }), 200
        
        # Validate part IDs are integers
        try:
            part_ids = [int(pid) for pid in part_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'All part IDs must be integers'}), 400
        
        # Verify all parts belong to the user
        user_parts = Part.query.filter(
            Part.id.in_(part_ids),
            Part.user_id == user_id
        ).all()
        
        if len(user_parts) != len(part_ids):
            found_ids = {part.id for part in user_parts}
            missing_ids = set(part_ids) - found_ids
            return jsonify({
                'error': f'Parts not found or not owned by you: {missing_ids}'
            }), 403
        
        # Check compatibility
        result = check_build_compatibility(part_ids)
        
        return jsonify(result), 200
        
    except NotFoundError as e:
        return jsonify({'error': e.message}), 404
    except Exception as e:
        logger.error(f'Error checking compatibility: {e}', exc_info=True)
        return jsonify({'error': 'Failed to check compatibility'}), 500


@bp.route('/rules', methods=['GET'])
def get_rules() -> Tuple[Dict[str, Any], int]:
    """Get all active compatibility rules."""
    try:
        rules = CompatibilityRule.query.filter_by(is_active=True).all()
        
        return jsonify({
            'rules': [rule.to_dict() for rule in rules],
            'count': len(rules)
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting rules: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve rules'}), 500


@bp.route('/rules', methods=['POST'])
def create_rule() -> Tuple[Dict[str, Any], int]:
    """Create a new compatibility rule."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        required_fields = ['part_type_1', 'part_type_2', 'rule_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        rule = CompatibilityRule(
            part_type_1=data['part_type_1'],
            part_type_2=data['part_type_2'],
            rule_type=data['rule_type'],
            rule_data=data.get('rule_data', {})
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify(rule.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating rule: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create rule'}), 500
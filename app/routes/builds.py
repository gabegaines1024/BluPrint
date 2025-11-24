"""API routes for PC builds management."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.database import db
from app.models import Build, Part
from app.services.compatibility_service import (
    check_build_compatibility,
    calculate_build_price
)
from app.utils.validation import validate_build_data
from app.exceptions import ValidationError, NotFoundError, AuthorizationError

bp = Blueprint('builds', __name__)
logger = logging.getLogger(__name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_builds() -> Tuple[Dict[str, Any], int]:
    """Get a list of builds (user's builds only)."""
    try:
        user_id = get_jwt_identity()
        builds = Build.query.filter_by(user_id=user_id).all()
        return jsonify([build.to_dict() for build in builds]), 200
        
    except Exception as e:
        logger.error(f'Error getting builds: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve builds'}), 500


@bp.route('/<int:build_id>', methods=['GET'])
@jwt_required()
def get_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Get a specific build by ID (must be owned by user)."""
    try:
        user_id = get_jwt_identity()
        build = Build.query.filter_by(id=build_id, user_id=user_id).first()
        
        if not build:
            raise NotFoundError('Build not found')
        
        return jsonify(build.to_dict()), 200
    except NotFoundError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        logger.error(f'Error getting build {build_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve build'}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_build() -> Tuple[Dict[str, Any], int]:
    """Create a new PC build (owned by current user)."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input
        validate_build_data(data, is_update=False)
        
        part_ids = data['parts']
        
        # Verify all parts belong to the user
        user_parts = Part.query.filter(
            Part.id.in_(part_ids),
            Part.user_id == user_id
        ).all()
        
        if len(user_parts) != len(part_ids):
            found_ids = {part.id for part in user_parts}
            missing_ids = set(part_ids) - found_ids
            raise ValidationError(f'Parts not found or not owned by you: {missing_ids}')
        
        # Check compatibility
        compat_result = check_build_compatibility(part_ids)
        
        # Calculate total price
        total_price = calculate_build_price(part_ids)
        
        # Create build
        build = Build(
            user_id=user_id,
            name=data['name'].strip(),
            description=data.get('description'),
            parts=part_ids,
            total_price=total_price,
            is_compatible=compat_result['is_compatible'],
            compatibility_issues=compat_result.get('issues', [])
        )
        
        db.session.add(build)
        db.session.commit()
        
        build_dict = build.to_dict()
        build_dict['compatibility_warnings'] = compat_result.get('warnings', [])
        
        logger.info(f'Build created: {build.id} by user {user_id}')
        return jsonify(build_dict), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except NotFoundError as e:
        return jsonify({'error': e.message}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating build: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create build'}), 500


@bp.route('/<int:build_id>', methods=['PUT'])
@jwt_required()
def update_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Update an existing build (must be owned by user)."""
    try:
        user_id = get_jwt_identity()
        build = Build.query.filter_by(id=build_id, user_id=user_id).first()
        
        if not build:
            raise NotFoundError('Build not found')
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400
        
        # Validate input
        validate_build_data(data, is_update=True)
        
        # Track if parts changed (need to re-check compatibility)
        parts_changed = 'parts' in data and data['parts'] != build.parts
        
        # Update fields
        if 'name' in data:
            build.name = data['name'].strip()
        if 'description' in data:
            build.description = data['description']
        
        if parts_changed:
            part_ids = data['parts']
            
            # Verify all parts belong to the user
            user_parts = Part.query.filter(
                Part.id.in_(part_ids),
                Part.user_id == user_id
            ).all()
            
            if len(user_parts) != len(part_ids):
                found_ids = {part.id for part in user_parts}
                missing_ids = set(part_ids) - found_ids
                raise ValidationError(f'Parts not found or not owned by you: {missing_ids}')
            
            # Re-check compatibility
            compat_result = check_build_compatibility(part_ids)
            
            # Recalculate price
            total_price = calculate_build_price(part_ids)
            
            build.parts = part_ids
            build.total_price = total_price
            build.is_compatible = compat_result['is_compatible']
            build.compatibility_issues = compat_result.get('issues', [])
        
        db.session.commit()
        
        build_dict = build.to_dict()
        if parts_changed:
            build_dict['compatibility_warnings'] = compat_result.get('warnings', [])
        
        logger.info(f'Build updated: {build_id} by user {user_id}')
        return jsonify(build_dict), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except NotFoundError as e:
        return jsonify({'error': e.message}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating build {build_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update build'}), 500


@bp.route('/<int:build_id>', methods=['DELETE'])
@jwt_required()
def delete_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete a build (must be owned by user)."""
    try:
        user_id = get_jwt_identity()
        build = Build.query.filter_by(id=build_id, user_id=user_id).first()
        
        if not build:
            raise NotFoundError('Build not found')
        
        db.session.delete(build)
        db.session.commit()
        
        logger.info(f'Build deleted: {build_id} by user {user_id}')
        return jsonify({'message': 'Build deleted successfully'}), 200
        
    except NotFoundError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting build {build_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete build'}), 500
"""API routes for PC builds management."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
import logging

from app.database import db
from app.models import Build
from app.services.compatibility_service import (
    check_build_compatibility,
    calculate_build_price
)
from app.utils.validation import validate_build_data
from app.exceptions import ValidationError, NotFoundError

bp = Blueprint('builds', __name__)
logger = logging.getLogger(__name__)


@bp.route('', methods=['GET'])
def get_builds() -> Tuple[Dict[str, Any], int]:
    """Get a list of builds."""
    try:
        builds = Build.query.all()
        return jsonify([build.to_dict() for build in builds]), 200
        
    except Exception as e:
        logger.error(f'Error getting builds: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve builds'}), 500


@bp.route('/<int:build_id>', methods=['GET'])
def get_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Get a specific build by ID."""
    try:
        build = Build.query.get_or_404(build_id)
        return jsonify(build.to_dict()), 200
    except Exception as e:
        logger.error(f'Error getting build {build_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve build'}), 500


@bp.route('', methods=['POST'])
def create_build() -> Tuple[Dict[str, Any], int]:
    """Create a new PC build."""
    try:
        data = request.get_json()
        
        # Validate input
        validate_build_data(data, is_update=False)
        
        part_ids = data['parts']
        
        # Check compatibility
        compat_result = check_build_compatibility(part_ids)
        
        # Calculate total price
        total_price = calculate_build_price(part_ids)
        
        # Create build
        build = Build(
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
def update_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Update an existing build."""
    try:
        build = Build.query.get_or_404(build_id)
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
def delete_build(build_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete a build."""
    try:
        build = Build.query.get_or_404(build_id)
        db.session.delete(build)
        db.session.commit()
        
        return jsonify({'message': 'Build deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting build {build_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete build'}), 500
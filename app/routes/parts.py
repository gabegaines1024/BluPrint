"""API routes for PC parts management."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
import logging

from app.database import db
from app.models import Part
from app.utils.validation import validate_part_data
from app.exceptions import ValidationError

bp = Blueprint('parts', __name__)
logger = logging.getLogger(__name__)


@bp.route('', methods=['GET'])
def get_parts() -> Tuple[Dict[str, Any], int]:
    """Get a list of parts with optional filtering."""
    try:
        query = Part.query
        
        # Apply filters
        part_type = request.args.get('part_type')
        if part_type:
            query = query.filter(Part.part_type == part_type)
        
        manufacturer = request.args.get('manufacturer')
        if manufacturer:
            query = query.filter(Part.manufacturer.ilike(f'%{manufacturer}%'))
        
        min_price = request.args.get('min_price', type=float)
        if min_price is not None:
            query = query.filter(Part.price >= min_price)
        
        max_price = request.args.get('max_price', type=float)
        if max_price is not None:
            query = query.filter(Part.price <= max_price)
        
        search = request.args.get('search')
        if search:
            query = query.filter(Part.name.ilike(f'%{search}%'))
        
        parts = query.all()
        
        return jsonify([part.to_dict() for part in parts]), 200
        
    except Exception as e:
        logger.error(f'Error getting parts: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve parts'}), 500


@bp.route('/<int:part_id>', methods=['GET'])
def get_part(part_id: int) -> Tuple[Dict[str, Any], int]:
    """Get a specific part by ID."""
    try:
        part = Part.query.get_or_404(part_id)
        return jsonify(part.to_dict()), 200
    except Exception as e:
        logger.error(f'Error getting part {part_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve part'}), 500


@bp.route('', methods=['POST'])
def create_part() -> Tuple[Dict[str, Any], int]:
    """Create a new part."""
    try:
        data = request.get_json()
        
        # Validate input
        validate_part_data(data, is_update=False)
        
        # Create part
        part = Part(
            name=data['name'].strip(),
            part_type=data['part_type'],
            manufacturer=data.get('manufacturer'),
            price=data.get('price'),
            specifications=data.get('specifications', {})
        )
        
        db.session.add(part)
        db.session.commit()
        
        return jsonify(part.to_dict()), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating part: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create part'}), 500


@bp.route('/<int:part_id>', methods=['PUT'])
def update_part(part_id: int) -> Tuple[Dict[str, Any], int]:
    """Update an existing part."""
    try:
        part = Part.query.get_or_404(part_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400
        
        # Validate input
        validate_part_data(data, is_update=True)
        
        # Update fields
        if 'name' in data:
            part.name = data['name'].strip()
        if 'part_type' in data:
            part.part_type = data['part_type']
        if 'manufacturer' in data:
            part.manufacturer = data['manufacturer']
        if 'price' in data:
            part.price = data['price']
        if 'specifications' in data:
            part.specifications = data['specifications']
        
        db.session.commit()
        
        return jsonify(part.to_dict()), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating part {part_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update part'}), 500


@bp.route('/<int:part_id>', methods=['DELETE'])
def delete_part(part_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete a part."""
    try:
        part = Part.query.get_or_404(part_id)
        
        db.session.delete(part)
        db.session.commit()
        
        return jsonify({'message': 'Part deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting part {part_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete part'}), 500
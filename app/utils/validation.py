"""Input validation utilities for API endpoints."""

from typing import Dict, Any, Optional, Tuple
from app.exceptions import ValidationError
from app.utils.spec_validation import validate_specifications


def validate_part_data(data: Optional[Dict[str, Any]], is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate part data before creating or updating.
    
    Args:
        data: Dictionary containing part data to validate.
        is_update: Whether this is an update operation (more lenient).
    
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    
    Raises:
        ValidationError: If validation fails and is_update is False.
    """
    if not data:
        if is_update:
            return False, 'No data provided for update'
        raise ValidationError('Request body is required')
    
    # Required fields (only for creation)
    if not is_update:
        if not data.get('name') or not isinstance(data['name'], str):
            raise ValidationError('Name is required and must be a string')
        
        if not data.get('part_type') or not isinstance(data['part_type'], str):
            raise ValidationError('Part type is required and must be a string')
    
    # Validate name if provided (update or create)
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str):
            raise ValidationError('Name must be a string')
        if len(name.strip()) == 0:
            raise ValidationError('Name cannot be empty')
        if len(name) > 200:
            raise ValidationError('Name cannot exceed 200 characters')
    
    # Validate price if provided
    if 'price' in data and data['price'] is not None:
        price = data['price']
        if not isinstance(price, (int, float)):
            raise ValidationError('Price must be a number')
        if price < 0:
            raise ValidationError('Price cannot be negative')
    
    # Validate manufacturer if provided
    if 'manufacturer' in data and data['manufacturer'] is not None:
        manufacturer = data['manufacturer']
        if not isinstance(manufacturer, str):
            raise ValidationError('Manufacturer must be a string')
        if len(manufacturer) > 100:
            raise ValidationError('Manufacturer cannot exceed 100 characters')
    
    # Validate specifications if provided
    if 'specifications' in data and data['specifications'] is not None:
        part_type = data.get('part_type')
        if part_type:
            # Validate against schema for part type
            try:
                data['specifications'] = validate_specifications(part_type, data['specifications'])
            except ValidationError:
                raise  # Re-raise validation errors
        elif not isinstance(data['specifications'], dict):
            raise ValidationError('Specifications must be a JSON object')
    
    return True, None


def validate_build_data(data: Optional[Dict[str, Any]], is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate build data before creating or updating.
    
    Args:
        data: Dictionary containing build data to validate.
        is_update: Whether this is an update operation.
    
    Returns:
        Tuple of (is_valid, error_message).
    
    Raises:
        ValidationError: If validation fails and is_update is False.
    """
    if not data:
        if is_update:
            return False, 'No data provided for update'
        raise ValidationError('Request body is required')
    
    # Required fields for creation
    if not is_update:
        if not data.get('name') or not isinstance(data['name'], str):
            raise ValidationError('Build name is required and must be a string')
        
        if len(data['name'].strip()) == 0:
            raise ValidationError('Build name cannot be empty')
        
        if len(data['name']) > 200:
            raise ValidationError('Build name cannot exceed 200 characters')
        
        # Validate parts array
        parts = data.get('parts', [])
        if not isinstance(parts, list):
            raise ValidationError('Parts must be an array')
        
        if len(parts) == 0:
            raise ValidationError('Build must contain at least one part')
        
        # Validate part IDs are integers
        for part_id in parts:
            if not isinstance(part_id, int):
                raise ValidationError('All part IDs must be integers')
    
    # Validate name if provided (for updates)
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str):
            raise ValidationError('Name must be a string')
        if len(name.strip()) == 0:
            raise ValidationError('Name cannot be empty')
    
    # Validate parts if provided (for updates)
    if 'parts' in data:
        parts = data['parts']
        if not isinstance(parts, list):
            raise ValidationError('Parts must be an array')
        for part_id in parts:
            if not isinstance(part_id, int):
                raise ValidationError('All part IDs must be integers')
    
    # Validate description if provided
    if 'description' in data and data['description'] is not None:
        if not isinstance(data['description'], str):
            raise ValidationError('Description must be a string')
    
    return True, None
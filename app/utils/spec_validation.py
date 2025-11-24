"""Specification validation schemas for different part types."""

from typing import Dict, Any, Optional
import jsonschema
from app.exceptions import ValidationError

# JSON schemas for different part types
PART_SPEC_SCHEMAS: Dict[str, Dict[str, Any]] = {
    'CPU': {
        'type': 'object',
        'properties': {
            'socket': {'type': 'string'},
            'core_count': {'type': 'number', 'minimum': 1},
            'thread_count': {'type': 'number', 'minimum': 1},
            'clock_speed': {'type': 'number', 'minimum': 0},
            'boost_clock': {'type': 'number', 'minimum': 0},
            'tdp': {'type': 'number', 'minimum': 0},
            'power_consumption': {'type': 'number', 'minimum': 0},
            'manufacturing_process': {'type': 'string'},
            'integrated_graphics': {'type': 'boolean'}
        },
        'additionalProperties': True
    },
    'GPU': {
        'type': 'object',
        'properties': {
            'memory_size': {'type': 'number', 'minimum': 0},
            'memory_type': {'type': 'string'},
            'clock_speed': {'type': 'number', 'minimum': 0},
            'boost_clock': {'type': 'number', 'minimum': 0},
            'cuda_cores': {'type': 'number', 'minimum': 0},
            'tdp': {'type': 'number', 'minimum': 0},
            'power_consumption': {'type': 'number', 'minimum': 0},
            'pcie_slot': {'type': 'string'},
            'length': {'type': 'number', 'minimum': 0},
            'width': {'type': 'number', 'minimum': 0}
        },
        'additionalProperties': True
    },
    'RAM': {
        'type': 'object',
        'properties': {
            'memory_size': {'type': 'number', 'minimum': 0},
            'speed': {'type': 'number', 'minimum': 0},
            'type': {'type': 'string'},
            'cas_latency': {'type': 'number', 'minimum': 0},
            'voltage': {'type': 'number', 'minimum': 0},
            'form_factor': {'type': 'string'},
            'modules': {'type': 'number', 'minimum': 1}
        },
        'additionalProperties': True
    },
    'Motherboard': {
        'type': 'object',
        'properties': {
            'socket': {'type': 'string'},
            'form_factor': {'type': 'string'},
            'chipset': {'type': 'string'},
            'memory_slots': {'type': 'number', 'minimum': 0},
            'max_memory': {'type': 'number', 'minimum': 0},
            'memory_type': {'type': 'string'},
            'pcie_slots': {'type': 'number', 'minimum': 0},
            'sata_ports': {'type': 'number', 'minimum': 0},
            'm2_slots': {'type': 'number', 'minimum': 0},
            'usb_ports': {'type': 'number', 'minimum': 0}
        },
        'additionalProperties': True
    },
    'Storage': {
        'type': 'object',
        'properties': {
            'storage_capacity': {'type': 'number', 'minimum': 0},
            'interface': {'type': 'string'},
            'form_factor': {'type': 'string'},
            'read_speed': {'type': 'number', 'minimum': 0},
            'write_speed': {'type': 'number', 'minimum': 0},
            'rpm': {'type': 'number', 'minimum': 0},
            'cache': {'type': 'number', 'minimum': 0}
        },
        'additionalProperties': True
    },
    'PSU': {
        'type': 'object',
        'properties': {
            'wattage': {'type': 'number', 'minimum': 0},
            'efficiency_rating': {'type': 'string'},
            'modular': {'type': 'boolean'},
            'sata_connectors': {'type': 'number', 'minimum': 0},
            'pcie_connectors': {'type': 'number', 'minimum': 0},
            'cpu_connectors': {'type': 'number', 'minimum': 0}
        },
        'additionalProperties': True
    },
    'Case': {
        'type': 'object',
        'properties': {
            'form_factor': {'type': 'string'},
            'max_gpu_length': {'type': 'number', 'minimum': 0},
            'max_cpu_cooler_height': {'type': 'number', 'minimum': 0},
            'drive_bays': {'type': 'number', 'minimum': 0},
            'fan_support': {'type': 'string'},
            'dimensions': {'type': 'string'}
        },
        'additionalProperties': True
    },
    'Cooler': {
        'type': 'object',
        'properties': {
            'type': {'type': 'string'},
            'socket_compatibility': {'type': 'array', 'items': {'type': 'string'}},
            'height': {'type': 'number', 'minimum': 0},
            'tdp': {'type': 'number', 'minimum': 0},
            'noise_level': {'type': 'number', 'minimum': 0},
            'fan_size': {'type': 'number', 'minimum': 0}
        },
        'additionalProperties': True
    }
}


def validate_specifications(part_type: str, specifications: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate specifications against part type schema.
    
    Args:
        part_type: Type of part (CPU, GPU, etc.).
        specifications: Specifications dictionary to validate.
    
    Returns:
        Validated specifications dictionary.
    
    Raises:
        ValidationError: If specifications don't match schema.
    """
    if specifications is None:
        return {}
    
    if not isinstance(specifications, dict):
        raise ValidationError('Specifications must be a JSON object')
    
    # Get schema for part type
    schema = PART_SPEC_SCHEMAS.get(part_type)
    
    if not schema:
        # Unknown part type - allow any specifications but validate it's a dict
        return specifications
    
    try:
        # Validate against schema
        jsonschema.validate(instance=specifications, schema=schema)
        return specifications
    except jsonschema.ValidationError as e:
        raise ValidationError(f'Invalid specifications for {part_type}: {e.message}')
    except jsonschema.SchemaError as e:
        raise ValidationError(f'Schema error: {e.message}')


def get_required_specs(part_type: str) -> list:
    """Get list of recommended (not required) specifications for a part type.
    
    Args:
        part_type: Type of part.
    
    Returns:
        List of recommended specification keys.
    """
    schema = PART_SPEC_SCHEMAS.get(part_type)
    if not schema:
        return []
    
    return list(schema.get('properties', {}).keys())


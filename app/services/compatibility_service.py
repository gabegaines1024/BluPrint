"""Service for checking PC part compatibility."""

from typing import List, Dict, Any, Optional
from app.models import Part, CompatibilityRule
from app.database import db
from app.exceptions import NotFoundError


def check_build_compatibility(part_ids: List[int]) -> Dict[str, Any]:
    """Check if a list of parts are compatible with each other.
    
    This function evaluates all parts in a build against compatibility rules
    and returns a detailed compatibility report.
    
    Args:
        part_ids: List of part IDs to check for compatibility.
    
    Returns:
        Dictionary containing:
            - is_compatible: Boolean indicating overall compatibility
            - issues: List of compatibility issues found
            - warnings: List of warnings (non-critical issues)
    
    Raises:
        NotFoundError: If any part ID does not exist.
    """
    if not part_ids:
        return {
            'is_compatible': True,
            'issues': [],
            'warnings': []
        }
    
    # Fetch all parts in one query (eager loading)
    parts = Part.query.filter(Part.id.in_(part_ids)).all()
    
    if len(parts) != len(part_ids):
        found_ids = {part.id for part in parts}
        missing_ids = set(part_ids) - found_ids
        raise NotFoundError(f"Parts not found: {', '.join(map(str, missing_ids))}")
    
    # Fetch all active compatibility rules
    rules = CompatibilityRule.query.filter_by(is_active=True).all()
    
    issues: List[str] = []
    warnings: List[str] = []
    
    # Group parts by type for easier checking
    parts_by_type: Dict[str, List[Part]] = {}
    for part in parts:
        parts_by_type.setdefault(part.part_type, []).append(part)
    
    # Separate power_requirement rules (they need all parts, not pairs)
    pairwise_rules = [r for r in rules if r.rule_type != 'power_requirement']
    power_rules = [r for r in rules if r.rule_type == 'power_requirement']
    
    # Check power requirement rules (operate on all parts)
    for rule in power_rules:
        power_result = _check_power_requirement(parts, parts_by_type)
        if not power_result['is_compatible']:
            issues.append(power_result['reason'])
        elif power_result.get('warning'):
            warnings.append(power_result['warning'])
    
    # Check pairwise rules (socket_match, form_factor, interface_match, etc.)
    for rule in pairwise_rules:
        part_type_1_parts = parts_by_type.get(rule.part_type_1, [])
        part_type_2_parts = parts_by_type.get(rule.part_type_2, [])
        
        # Skip if neither part type is in the build
        if not part_type_1_parts and not part_type_2_parts:
            continue
        
        # Evaluate rule for all combinations
        for part1 in part_type_1_parts:
            for part2 in part_type_2_parts:
                if part1.id == part2.id:
                    continue  # Skip same part
                
                compat_result = _evaluate_rule(rule, part1, part2)
                if not compat_result['is_compatible']:
                    issues.append(compat_result['reason'])
                elif compat_result.get('warning'):
                    warnings.append(compat_result['warning'])
    
    # Additional validation checks
    _check_required_part_types(parts_by_type, issues)
    
    return {
        'is_compatible': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }


def check_part_compatibility(part1: Part, part2: Part) -> Dict[str, Any]:
    """Check if two specific parts are compatible.
    
    Args:
        part1: First part to check.
        part2: Second part to check.
    
    Returns:
        Dictionary containing:
            - is_compatible: Boolean indicating compatibility
            - reason: String explaining incompatibility (if any)
    """
    if part1.id == part2.id:
        return {
            'is_compatible': True,
            'reason': None
        }
    
    # Get applicable rules
    rules = CompatibilityRule.query.filter(
        CompatibilityRule.is_active == True,
        db.or_(
            db.and_(
                CompatibilityRule.part_type_1 == part1.part_type,
                CompatibilityRule.part_type_2 == part2.part_type
            ),
            db.and_(
                CompatibilityRule.part_type_1 == part2.part_type,
                CompatibilityRule.part_type_2 == part1.part_type
            )
        )
    ).all()
    
    for rule in rules:
        # Determine order based on rule
        p1 = part1 if rule.part_type_1 == part1.part_type else part2
        p2 = part2 if rule.part_type_2 == part2.part_type else part1
        
        result = _evaluate_rule(rule, p1, p2)
        if not result['is_compatible']:
            return result
    
    return {
        'is_compatible': True,
        'reason': None
    }


def calculate_build_price(part_ids: List[int]) -> float:
    """Calculate total price for a list of parts.
    
    Args:
        part_ids: List of part IDs.
    
    Returns:
        Total price of all parts.
    
    Raises:
        NotFoundError: If any part ID does not exist.
    """
    if not part_ids:
        return 0.0
    
    parts = Part.query.filter(Part.id.in_(part_ids)).all()
    
    if len(parts) != len(part_ids):
        found_ids = {part.id for part in parts}
        missing_ids = set(part_ids) - found_ids
        raise NotFoundError(f"Parts not found: {', '.join(map(str, missing_ids))}")
    
    total = sum(part.price or 0.0 for part in parts)
    return round(total, 2)


def _evaluate_rule(rule: CompatibilityRule, part1: Part, part2: Part) -> Dict[str, Any]:
    """Evaluate a compatibility rule against two parts.
    
    Args:
        rule: Compatibility rule to evaluate.
        part1: First part.
        part2: Second part.
    
    Returns:
        Dictionary with compatibility result and reason.
    """
    rule_type = rule.rule_type
    rule_data = rule.rule_data or {}
    specs1 = part1.specifications or {}
    specs2 = part2.specifications or {}
    
    if rule_type == 'socket_match':
        # Validate socket compatibility between CPU and Motherboard.
        # Requirements:
        # - Both parts MUST have a socket specification defined
        # - Socket values must be non-empty strings
        # - Socket values must match exactly (case-sensitive, whitespace-sensitive)
        socket1_raw = specs1.get('socket')
        socket2_raw = specs2.get('socket')
        
        # Normalize socket values: convert to string and strip whitespace
        socket1 = str(socket1_raw).strip() if socket1_raw is not None else None
        socket2 = str(socket2_raw).strip() if socket2_raw is not None else None
        
        # Validation: Check for missing or empty socket fields (critical)
        socket1_missing = not socket1 or socket1 == ''
        socket2_missing = not socket2 or socket2 == ''
        
        if socket1_missing and socket2_missing:
            return {
                'is_compatible': False,
                'reason': f"{part1.name} ({part1.part_type}) and {part2.name} ({part2.part_type}) are both missing socket specifications. Socket type is required for compatibility checking."
            }
        elif socket1_missing:
            return {
                'is_compatible': False,
                'reason': f"{part1.name} ({part1.part_type}) is missing a socket specification. Socket type is required for compatibility checking."
            }
        elif socket2_missing:
            return {
                'is_compatible': False,
                'reason': f"{part2.name} ({part2.part_type}) is missing a socket specification. Socket type is required for compatibility checking."
            }
        
        # Match requirement: Both sockets exist - verify they match exactly
        if socket1 != socket2:
            return {
                'is_compatible': False,
                'reason': f"{part1.name} (socket: {socket1}) is incompatible with {part2.name} (socket: {socket2}). Socket types must match exactly."
            }
        
        # Success: Sockets match exactly - compatible
        return {
            'is_compatible': True,
            'reason': None
        }
    
    elif rule_type == 'form_factor':
        # Check form factor compatibility between Case and Motherboard.
        # Standard hierarchy:
        # - ATX cases support: ATX, mATX, ITX
        # - mATX cases support: mATX, ITX
        # - ITX cases support: ITX only
        
        # Define the compatibility hierarchy mapping case form factors to supported motherboard form factors
        FORM_FACTOR_HIERARCHY = {
            'ATX': ['ATX', 'mATX', 'ITX'],
            'mATX': ['mATX', 'ITX'],
            'ITX': ['ITX']
        }
        
        # Identify which part is the Case and which is the Motherboard
        case_part = None
        motherboard_part = None
        
        if part1.part_type == 'Case' and part2.part_type == 'Motherboard':
            case_part = part1
            motherboard_part = part2
        elif part1.part_type == 'Motherboard' and part2.part_type == 'Case':
            case_part = part2
            motherboard_part = part1
        else:
            # If the rule is applied to wrong part types, skip silently
            # (This shouldn't happen if rules are configured correctly)
            return {
                'is_compatible': True,
                'reason': None
            }
        
        case_specs = case_part.specifications or {}
        motherboard_specs = motherboard_part.specifications or {}
        
        case_form_factor_raw = case_specs.get('form_factor')
        motherboard_form_factor_raw = motherboard_specs.get('form_factor')
        
        # Normalize form factor values: convert to string and strip whitespace, handle case variations
        case_form_factor = None
        motherboard_form_factor = None
        
        if case_form_factor_raw is not None:
            case_ff_str = str(case_form_factor_raw).strip().upper()
            # Normalize common variations to standard format
            if case_ff_str in ['MATX', 'MICRO-ATX', 'MICRO ATX', 'MICROATX']:
                case_form_factor = 'mATX'
            elif case_ff_str == 'ATX':
                case_form_factor = 'ATX'
            elif case_ff_str == 'ITX':
                case_form_factor = 'ITX'
            else:
                # Preserve original value if not recognized
                case_form_factor = str(case_form_factor_raw).strip()
        
        if motherboard_form_factor_raw is not None:
            mb_ff_str = str(motherboard_form_factor_raw).strip().upper()
            # Normalize common variations to standard format
            if mb_ff_str in ['MATX', 'MICRO-ATX', 'MICRO ATX', 'MICROATX']:
                motherboard_form_factor = 'mATX'
            elif mb_ff_str == 'ATX':
                motherboard_form_factor = 'ATX'
            elif mb_ff_str == 'ITX':
                motherboard_form_factor = 'ITX'
            else:
                # Preserve original value if not recognized
                motherboard_form_factor = str(motherboard_form_factor_raw).strip()
        
        # Validation: Check for missing form factor specifications
        case_form_factor_missing = not case_form_factor or case_form_factor == ''
        motherboard_form_factor_missing = not motherboard_form_factor or motherboard_form_factor == ''
        
        if case_form_factor_missing and motherboard_form_factor_missing:
            return {
                'is_compatible': False,
                'reason': f"{case_part.name} (Case) and {motherboard_part.name} (Motherboard) are both missing form factor specifications. Form factor is required for compatibility checking."
            }
        elif case_form_factor_missing:
            return {
                'is_compatible': False,
                'reason': f"{case_part.name} (Case) is missing a form factor specification. Form factor is required to determine if the motherboard will fit."
            }
        elif motherboard_form_factor_missing:
            return {
                'is_compatible': False,
                'reason': f"{motherboard_part.name} (Motherboard) is missing a form factor specification. Form factor is required to determine if it will fit in the case."
            }
        
        # Check compatibility using the hierarchy
        # Get the list of motherboard form factors supported by the case
        supported_motherboard_form_factors = FORM_FACTOR_HIERARCHY.get(case_form_factor)
        
        if supported_motherboard_form_factors is None:
            # Unknown case form factor - return warning but don't fail
            return {
                'is_compatible': True,
                'warning': f"Unknown case form factor '{case_form_factor}' for {case_part.name}. Compatibility check skipped."
            }
        
        # Check if the motherboard form factor is supported by the case
        if motherboard_form_factor not in supported_motherboard_form_factors:
            return {
                'is_compatible': False,
                'reason': f"Motherboard {motherboard_part.name} ({motherboard_form_factor}) is too large for Case {case_part.name} ({case_form_factor}). Case supports: {', '.join(supported_motherboard_form_factors)}."
            }
        
        # Success: Motherboard form factor is compatible with case
        return {
            'is_compatible': True,
            'reason': None
        }
    
    
    elif rule_type == 'interface_match':
        # Check interface compatibility (e.g., SATA, NVMe)
        interface1 = specs1.get('interface')
        interface2 = specs2.get('interface')
        required_interface = rule_data.get('required_interface')
        if required_interface:
            if interface1 != required_interface and interface2 != required_interface:
                return {
                    'is_compatible': False,
                    'reason': f"Interface mismatch: {required_interface} required"
                }
    
    return {
        'is_compatible': True,
        'reason': None
    }


def _check_power_requirement(all_parts: List[Part], 
                             parts_by_type: Dict[str, List[Part]]) -> Dict[str, Any]:
    """Check if total power consumption of all parts exceeds PSU capacity.
    
    This function:
    1. Identifies the PSU part(s) in the build
    2. Sums power consumption from all non-PSU parts
    3. Compares total consumption against PSU wattage
    
    Args:
        all_parts: List of all parts in the build.
        parts_by_type: Dictionary grouping parts by their type.
    
    Returns:
        Dictionary containing:
            - is_compatible: Boolean indicating compatibility
            - reason: String explaining incompatibility (if any)
            - warning: Optional warning message
    """
    # Find PSU part(s)
    psu_parts = parts_by_type.get('PSU', [])
    
    # Validation: Check if PSU exists
    if not psu_parts:
        return {
            'is_compatible': False,
            'reason': 'Build is missing a Power Supply Unit (PSU). A PSU is required to power all components.'
        }
    
    # If multiple PSUs, use the one with highest wattage
    # (or could return an error/warning - for now, use the highest)
    psu = None
    max_wattage = 0
    for p in psu_parts:
        specs = p.specifications or {}
        wattage = specs.get('wattage')
        if wattage is not None:
            try:
                wattage_float = float(wattage)
                if wattage_float > max_wattage:
                    max_wattage = wattage_float
                    psu = p
            except (ValueError, TypeError):
                continue
    
    # Validation: Check if PSU has wattage specification
    if psu is None:
        if len(psu_parts) == 1:
            return {
                'is_compatible': False,
                'reason': f"{psu_parts[0].name} (PSU) is missing a wattage specification. PSU wattage is required for power compatibility checking."
            }
        else:
            return {
                'is_compatible': False,
                'reason': f"All PSU parts are missing wattage specifications. PSU wattage is required for power compatibility checking."
            }
    
    psu_specs = psu.specifications or {}
    psu_wattage = float(psu_specs.get('wattage'))
    
    # Sum power consumption from all non-PSU parts
    total_power_consumption = 0.0
    parts_missing_power_spec = []
    
    for part in all_parts:
        # Skip PSU parts
        if part.part_type == 'PSU':
            continue
        
        specs = part.specifications or {}
        power_consumption = specs.get('power_consumption')
        
        if power_consumption is None:
            # Parts missing power consumption spec
            parts_missing_power_spec.append(part.name)
        else:
            try:
                power_float = float(power_consumption)
                if power_float > 0:  # Only add positive values
                    total_power_consumption += power_float
            except (ValueError, TypeError):
                # Invalid power_consumption value
                parts_missing_power_spec.append(part.name)
    
    # Round to 2 decimal places for display
    total_power_consumption = round(total_power_consumption, 2)
    
    # Validation: Check for parts missing power consumption specs
    if parts_missing_power_spec:
        warning_msg = f"Some parts are missing power consumption specifications: {', '.join(parts_missing_power_spec)}. Power compatibility check may be inaccurate."
        # Return as warning, but continue with calculation
        result = {
            'is_compatible': True,
            'warning': warning_msg
        }
    else:
        result = {
            'is_compatible': True
        }
    
    # Compare total consumption against PSU wattage
    if total_power_consumption > psu_wattage:
        return {
            'is_compatible': False,
            'reason': f"Total power consumption ({total_power_consumption}W) exceeds PSU capacity ({psu_wattage}W). Build requires at least {total_power_consumption}W but PSU provides {psu_wattage}W."
        }
    
    return result


def _check_required_part_types(parts_by_type: Dict[str, List[Part]], 
                               issues: List[str]) -> None:
    """Check if required part types are present in the build.
    
    Args:
        parts_by_type: Dictionary grouping parts by their type.
        issues: List to append any issues found.
    """
    required_types = ['CPU', 'Motherboard']  # Minimal required parts
    
    for req_type in required_types:
        if req_type not in parts_by_type:
            issues.append(f"Missing required part type: {req_type}")
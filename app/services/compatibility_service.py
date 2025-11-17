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
    
    # Check each rule against the parts
    for rule in rules:
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
        # Check if CPU socket matches motherboard socket
        socket1 = specs1.get('socket')
        socket2 = specs2.get('socket')
        if socket1 and socket2 and socket1 != socket2:
            return {
                'is_compatible': False,
                'reason': f"{part1.name} (socket: {socket1}) is incompatible with "
                         f"{part2.name} (socket: {socket2})"
            }
    
    elif rule_type == 'form_factor':
        # Check form factor compatibility (e.g., motherboard and case)
        form_factor1 = specs1.get('form_factor')
        form_factor2 = specs2.get('form_factor')
        if form_factor1 and form_factor2:
            compatible_sizes = rule_data.get('compatible_sizes', [])
            if form_factor1 not in compatible_sizes or form_factor2 not in compatible_sizes:
                if form_factor1 != form_factor2:
                    return {
                        'is_compatible': False,
                        'reason': f"{part1.name} (form factor: {form_factor1}) may not fit "
                                 f"{part2.name} (form factor: {form_factor2})"
                    }
    
    elif rule_type == 'power_requirement':
        # Check power requirements
        power_req = specs1.get('power_consumption') or specs2.get('power_consumption')
        psu_wattage = specs1.get('wattage') or specs2.get('wattage')
        if power_req and psu_wattage and power_req > psu_wattage:
            return {
                'is_compatible': False,
                'reason': f"Power requirement ({power_req}W) exceeds PSU capacity ({psu_wattage}W)"
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
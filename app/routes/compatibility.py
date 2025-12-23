"""API routes for compatibility checking and rules management."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
    CompatibilityRuleCreate,
    CompatibilityRuleResponse
)
from app.models import CompatibilityRule, Part, User
from app.dependencies import get_current_user
from app.services.compatibility_service import check_build_compatibility
from app.exceptions import NotFoundError

router = APIRouter(prefix="/api/v1/compatibility", tags=["Compatibility"])
logger = logging.getLogger(__name__)


@router.post("/check", response_model=CompatibilityCheckResponse)
async def check_compatibility(
    request_data: CompatibilityCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check compatibility of a list of parts (must be owned by user).
    
    Args:
        request_data: Compatibility check request with part IDs.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        CompatibilityCheckResponse with compatibility results.
    
    Raises:
        HTTPException: If validation or compatibility check fails.
    """
    try:
        part_ids = request_data.part_ids
        
        if not part_ids:
            return CompatibilityCheckResponse(
                is_compatible=True,
                issues=[],
                warnings=[]
            )
        
        # Verify all parts belong to the user
        user_parts = db.query(Part).filter(
            Part.id.in_(part_ids),
            Part.user_id == current_user.id
        ).all()
        
        if len(user_parts) != len(part_ids):
            found_ids = {part.id for part in user_parts}
            missing_ids = set(part_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Parts not found or not owned by you: {missing_ids}'
            )
        
        # Check compatibility
        result = check_build_compatibility(part_ids)
        
        return CompatibilityCheckResponse(**result)
        
    except HTTPException:
        raise
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        logger.error(f'Error checking compatibility: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to check compatibility'
        )


@router.get("/rules", response_model=dict)
async def get_rules(db: Session = Depends(get_db)):
    """
    Get all active compatibility rules.
    
    Args:
        db: Database session.
    
    Returns:
        Dictionary with rules list and count.
    
    Raises:
        HTTPException: If retrieval fails.
    """
    try:
        rules = db.query(CompatibilityRule).filter(
            CompatibilityRule.is_active == True
        ).all()
        
        return {
            'rules': [CompatibilityRuleResponse.model_validate(rule) for rule in rules],
            'count': len(rules)
        }
        
    except Exception as e:
        logger.error(f'Error getting rules: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve rules'
        )


@router.post("/rules", response_model=CompatibilityRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: CompatibilityRuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new compatibility rule.
    
    Args:
        rule_data: Compatibility rule creation data.
        db: Database session.
    
    Returns:
        CompatibilityRuleResponse with created rule data.
    
    Raises:
        HTTPException: If creation fails.
    """
    try:
        rule = CompatibilityRule(
            part_type_1=rule_data.part_type_1,
            part_type_2=rule_data.part_type_2,
            rule_type=rule_data.rule_type,
            rule_data=rule_data.rule_data or {}
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        return CompatibilityRuleResponse.model_validate(rule)
        
    except Exception as e:
        db.rollback()
        logger.error(f'Error creating rule: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create rule'
        )

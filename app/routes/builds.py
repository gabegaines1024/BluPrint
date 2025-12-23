"""API routes for PC builds management."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BuildCreate, BuildUpdate, BuildResponse
from app.models import Build, Part, User
from app.dependencies import get_current_user
from app.services.compatibility_service import (
    check_build_compatibility,
    calculate_build_price
)
from app.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/api/v1/builds", tags=["Builds"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[BuildResponse])
async def get_builds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of builds (user's builds only).
    
    Args:
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        List of BuildResponse objects.
    """
    try:
        builds = db.query(Build).filter(Build.user_id == current_user.id).all()
        return [BuildResponse.model_validate(build) for build in builds]
        
    except Exception as e:
        logger.error(f'Error getting builds: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve builds'
        )


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific build by ID (must be owned by user).
    
    Args:
        build_id: Build ID to retrieve.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        BuildResponse object.
    
    Raises:
        HTTPException: If build not found.
    """
    try:
        build = db.query(Build).filter(
            Build.id == build_id,
            Build.user_id == current_user.id
        ).first()
        
        if not build:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Build not found'
            )
        
        return BuildResponse.model_validate(build)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error getting build {build_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve build'
        )


@router.post("", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_data: BuildCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new PC build (owned by current user).
    
    Args:
        build_data: Build creation data.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        BuildResponse with created build data.
    
    Raises:
        HTTPException: If creation fails.
    """
    try:
        part_ids = build_data.parts
        
        # Verify all parts belong to the user
        user_parts = db.query(Part).filter(
            Part.id.in_(part_ids),
            Part.user_id == current_user.id
        ).all()
        
        if len(user_parts) != len(part_ids):
            found_ids = {part.id for part in user_parts}
            missing_ids = set(part_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Parts not found or not owned by you: {missing_ids}'
            )
        
        # Check compatibility
        compat_result = check_build_compatibility(part_ids)
        
        # Calculate total price
        total_price = calculate_build_price(part_ids)
        
        # Create build
        build = Build(
            user_id=current_user.id,
            name=build_data.name.strip(),
            description=build_data.description,
            parts=part_ids,
            total_price=total_price,
            is_compatible=compat_result['is_compatible'],
            compatibility_issues=compat_result.get('issues', [])
        )
        
        db.add(build)
        db.commit()
        db.refresh(build)
        
        # Add warnings to response
        build_response = BuildResponse.model_validate(build)
        build_response.compatibility_warnings = compat_result.get('warnings', [])
        
        logger.info(f'Build created: {build.id} by user {current_user.id}')
        return build_response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f'Error creating build: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create build'
        )


@router.put("/{build_id}", response_model=BuildResponse)
async def update_build(
    build_id: int,
    build_data: BuildUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing build (must be owned by user).
    
    Args:
        build_id: Build ID to update.
        build_data: Build update data.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        BuildResponse with updated build data.
    
    Raises:
        HTTPException: If build not found or update fails.
    """
    try:
        build = db.query(Build).filter(
            Build.id == build_id,
            Build.user_id == current_user.id
        ).first()
        
        if not build:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Build not found'
            )
        
        update_data = build_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No data provided for update'
            )
        
        # Track if parts changed (need to re-check compatibility)
        parts_changed = 'parts' in update_data and update_data['parts'] != build.parts
        compat_warnings = []
        
        # Update basic fields
        if 'name' in update_data:
            build.name = update_data['name'].strip()
        if 'description' in update_data:
            build.description = update_data['description']
        
        if parts_changed:
            part_ids = update_data['parts']
            
            # Verify all parts belong to the user
            user_parts = db.query(Part).filter(
                Part.id.in_(part_ids),
                Part.user_id == current_user.id
            ).all()
            
            if len(user_parts) != len(part_ids):
                found_ids = {part.id for part in user_parts}
                missing_ids = set(part_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Parts not found or not owned by you: {missing_ids}'
                )
            
            # Re-check compatibility
            compat_result = check_build_compatibility(part_ids)
            
            # Recalculate price
            total_price = calculate_build_price(part_ids)
            
            build.parts = part_ids
            build.total_price = total_price
            build.is_compatible = compat_result['is_compatible']
            build.compatibility_issues = compat_result.get('issues', [])
            compat_warnings = compat_result.get('warnings', [])
        
        db.commit()
        db.refresh(build)
        
        build_response = BuildResponse.model_validate(build)
        if parts_changed:
            build_response.compatibility_warnings = compat_warnings
        
        logger.info(f'Build updated: {build_id} by user {current_user.id}')
        return build_response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f'Error updating build {build_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update build'
        )


@router.delete("/{build_id}", status_code=status.HTTP_200_OK)
async def delete_build(
    build_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a build (must be owned by user).
    
    Args:
        build_id: Build ID to delete.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        Success message.
    
    Raises:
        HTTPException: If build not found or deletion fails.
    """
    try:
        build = db.query(Build).filter(
            Build.id == build_id,
            Build.user_id == current_user.id
        ).first()
        
        if not build:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Build not found'
            )
        
        db.delete(build)
        db.commit()
        
        logger.info(f'Build deleted: {build_id} by user {current_user.id}')
        return {"message": "Build deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f'Error deleting build {build_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete build'
        )

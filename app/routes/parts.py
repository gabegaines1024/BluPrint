"""API routes for PC parts management."""

from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PartCreate, PartUpdate, PartResponse
from app.models import Part, User
from app.dependencies import get_current_user
from app.utils.validation import validate_part_data
from app.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/api/v1/parts", tags=["Parts"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[PartResponse])
async def get_parts(
    part_type: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of parts with optional filtering (user's parts only).
    
    Args:
        part_type: Filter by part type.
        manufacturer: Filter by manufacturer (partial match).
        min_price: Filter by minimum price.
        max_price: Filter by maximum price.
        search: Search in part names.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        List of PartResponse objects.
    """
    try:
        query = db.query(Part).filter(Part.user_id == current_user.id)
        
        # Apply filters
        if part_type:
            query = query.filter(Part.part_type == part_type)
        
        if manufacturer:
            query = query.filter(Part.manufacturer.ilike(f'%{manufacturer}%'))
        
        if min_price is not None:
            query = query.filter(Part.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Part.price <= max_price)
        
        if search:
            query = query.filter(Part.name.ilike(f'%{search}%'))
        
        parts = query.all()
        return [PartResponse.model_validate(part) for part in parts]
        
    except Exception as e:
        logger.error(f'Error getting parts: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve parts'
        )


@router.get("/{part_id}", response_model=PartResponse)
async def get_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific part by ID (must be owned by user).
    
    Args:
        part_id: Part ID to retrieve.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        PartResponse object.
    
    Raises:
        HTTPException: If part not found or not owned by user.
    """
    try:
        part = db.query(Part).filter(
            Part.id == part_id,
            Part.user_id == current_user.id
        ).first()
        
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Part not found'
            )
        
        return PartResponse.model_validate(part)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error getting part {part_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve part'
        )


@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
async def create_part(
    part_data: PartCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new part (owned by current user).
    
    Args:
        part_data: Part creation data.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        PartResponse with created part data.
    
    Raises:
        HTTPException: If creation fails.
    """
    try:
        # Create part
        part = Part(
            user_id=current_user.id,
            name=part_data.name.strip(),
            part_type=part_data.part_type,
            manufacturer=part_data.manufacturer,
            price=part_data.price,
            specifications=part_data.specifications or {}
        )
        
        db.add(part)
        db.commit()
        db.refresh(part)
        
        logger.info(f'Part created: {part.id} by user {current_user.id}')
        return PartResponse.model_validate(part)
        
    except Exception as e:
        db.rollback()
        logger.error(f'Error creating part: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create part'
        )


@router.put("/{part_id}", response_model=PartResponse)
async def update_part(
    part_id: int,
    part_data: PartUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing part (must be owned by user).
    
    Args:
        part_id: Part ID to update.
        part_data: Part update data.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        PartResponse with updated part data.
    
    Raises:
        HTTPException: If part not found or update fails.
    """
    try:
        part = db.query(Part).filter(
            Part.id == part_id,
            Part.user_id == current_user.id
        ).first()
        
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Part not found'
            )
        
        # Update fields if provided
        update_data = part_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No data provided for update'
            )
        
        for field, value in update_data.items():
            if field == 'name' and value:
                setattr(part, field, value.strip())
            else:
                setattr(part, field, value)
        
        db.commit()
        db.refresh(part)
        
        logger.info(f'Part updated: {part_id} by user {current_user.id}')
        return PartResponse.model_validate(part)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f'Error updating part {part_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update part'
        )


@router.delete("/{part_id}", status_code=status.HTTP_200_OK)
async def delete_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a part (must be owned by user).
    
    Args:
        part_id: Part ID to delete.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        Success message.
    
    Raises:
        HTTPException: If part not found or deletion fails.
    """
    try:
        part = db.query(Part).filter(
            Part.id == part_id,
            Part.user_id == current_user.id
        ).first()
        
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Part not found'
            )
        
        db.delete(part)
        db.commit()
        
        logger.info(f'Part deleted: {part_id} by user {current_user.id}')
        return {"message": "Part deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f'Error deleting part {part_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete part'
        )
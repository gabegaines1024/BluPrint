"""API routes for authentication."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.exceptions import ValidationError, AuthenticationError, NotFoundError
from app.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (username, email, password).
        db: Database session.
    
    Returns:
        TokenResponse with user data and access token.
    
    Raises:
        HTTPException: If registration fails.
    """
    try:
        result = AuthService.register_user(
            user_data.username,
            user_data.email,
            user_data.password,
            db
        )
        
        logger.info(f'User registered: {user_data.username}')
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        logger.error(f'Error registering user: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to register user'
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return access token.
    
    Args:
        credentials: User login credentials (username, password).
        db: Database session.
    
    Returns:
        TokenResponse with user data and access token.
    
    Raises:
        HTTPException: If authentication fails.
    """
    try:
        result = AuthService.login_user(
            credentials.username,
            credentials.password,
            db
        )
        
        logger.info(f'User logged in: {credentials.username}')
        return result
        
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f'Error logging in user: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to authenticate user'
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from JWT token.
    
    Returns:
        UserResponse with current user data.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user information.
    
    Args:
        update_data: User update data (email, password).
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        UserResponse with updated user data.
    
    Raises:
        HTTPException: If update fails.
    """
    try:
        # Build update dict with only provided fields
        update_dict = {}
        if update_data.email is not None:
            update_dict['email'] = update_data.email
        if update_data.password is not None:
            update_dict['password'] = update_data.password
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No data provided for update'
            )
        
        user = AuthService.update_user(current_user.id, db, **update_dict)
        
        logger.info(f'User updated: {current_user.id}')
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        logger.error(f'Error updating user: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update user'
        )


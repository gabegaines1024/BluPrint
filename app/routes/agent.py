"""API routes for PC Building Agent."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ContextResponse,
    ResetResponse,
    SaveBuildRequest,
    BuildResponse
)
from app.models import Build, User
from app.dependencies import get_current_user
from app.services.agent_service import PCBuildingAgent
from app.services.compatibility_service import (
    check_build_compatibility,
    calculate_build_price
)
from app.exceptions import ValidationError

router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])
logger = logging.getLogger(__name__)

# Store conversation contexts per user (in production, use Redis or database)
_user_contexts: Dict[int, Dict[str, Any]] = {}


def get_agent() -> PCBuildingAgent:
    """Get or create agent instance."""
    return PCBuildingAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request_data: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the agent and get a response.
    
    Args:
        request_data: Chat request with user message.
        current_user: Current authenticated user.
    
    Returns:
        ChatResponse with agent message and recommendations.
    
    Raises:
        HTTPException: If message processing fails.
    """
    try:
        message = request_data.message.strip()
        
        # Get or initialize user context
        context = _user_contexts.get(current_user.id)
        
        # Process message
        agent = get_agent()
        result = agent.process_message(message, current_user.id, context)
        
        # Update stored context
        _user_contexts[current_user.id] = result['updated_context']
        
        # Format response
        return ChatResponse(
            message=result['message'],
            recommended_parts=result.get('recommended_parts', []),
            build_suggestion=result.get('build_suggestion')
        )
        
    except Exception as e:
        logger.error(f'Error in agent chat: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to process message'
        )


@router.get("/context", response_model=ContextResponse)
async def get_context(current_user: User = Depends(get_current_user)):
    """
    Get current conversation context.
    
    Args:
        current_user: Current authenticated user.
    
    Returns:
        ContextResponse with current conversation context.
    """
    try:
        context = _user_contexts.get(current_user.id, {})
        return ContextResponse(context=context)
        
    except Exception as e:
        logger.error(f'Error getting context: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get context'
        )


@router.post("/reset", response_model=ResetResponse)
async def reset(current_user: User = Depends(get_current_user)):
    """
    Reset the conversation context.
    
    Args:
        current_user: Current authenticated user.
    
    Returns:
        ResetResponse confirming reset.
    """
    try:
        _user_contexts[current_user.id] = {}
        return ResetResponse(message='Conversation reset successfully')
        
    except Exception as e:
        logger.error(f'Error resetting context: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to reset conversation'
        )


@router.post("/save-build", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def save_build(
    request_data: SaveBuildRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a build from the agent conversation.
    
    Args:
        request_data: Build save request with name, parts, and description.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        BuildResponse with saved build data.
    
    Raises:
        HTTPException: If save fails.
    """
    try:
        name = request_data.name.strip()
        part_ids = request_data.parts
        description = request_data.description
        
        # Check compatibility
        compat_result = check_build_compatibility(part_ids)
        
        # Calculate price
        total_price = calculate_build_price(part_ids)
        
        # Create build
        build = Build(
            user_id=current_user.id,
            name=name,
            description=description,
            parts=part_ids,
            total_price=total_price,
            is_compatible=compat_result['is_compatible'],
            compatibility_issues=compat_result.get('issues', [])
        )
        
        db.add(build)
        db.commit()
        db.refresh(build)
        
        logger.info(f'Build saved from agent: {build.id} by user {current_user.id}')
        return BuildResponse.model_validate(build)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        db.rollback()
        logger.error(f'Error saving build from agent: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to save build'
        )

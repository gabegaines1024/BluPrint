"""API routes for ML-based part recommendations."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    ModelStatusResponse
)
from app.models import Part, User
from app.dependencies import get_current_user
from app.ml_model.recommender import MLRecommender

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])
logger = logging.getLogger(__name__)

# Global recommender instance
_recommender: MLRecommender = None


def get_recommender() -> MLRecommender:
    """
    Get or create the ML recommender instance.
    
    Returns:
        MLRecommender instance.
    """
    global _recommender
    if _recommender is None:
        _recommender = MLRecommender()
    return _recommender


@router.post("/parts", response_model=RecommendationResponse)
async def recommend_parts(
    request_data: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ML-based part recommendations.
    
    Args:
        request_data: Recommendation request with preferences and constraints.
        current_user: Current authenticated user.
        db: Database session.
    
    Returns:
        RecommendationResponse with recommended parts and scores.
    
    Raises:
        HTTPException: If recommendation generation fails.
    """
    try:
        user_preferences = {
            'part_type': request_data.part_type,
            'budget': request_data.budget,
            'min_performance': request_data.min_performance,
            'budget_ratio': request_data.budget_ratio
        }
        
        existing_parts = request_data.existing_parts or []
        
        # Verify existing parts belong to user
        if existing_parts:
            user_parts = db.query(Part).filter(
                Part.id.in_(existing_parts),
                Part.user_id == current_user.id
            ).all()
            if len(user_parts) != len(existing_parts):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Some existing parts not found or not owned by you'
                )
        
        # Get recommendations (filtered by user's parts)
        recommender = get_recommender()
        recommendations = recommender.recommend_parts(
            user_preferences=user_preferences,
            budget=request_data.budget,
            existing_parts=existing_parts if existing_parts else None,
            num_recommendations=request_data.num_recommendations,
            user_id=current_user.id  # Filter by user
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            count=len(recommendations),
            model_version=recommender.model_version if recommender.is_available() else 'rule-based'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error generating recommendations: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to generate recommendations'
        )


@router.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    """
    Get status of the ML recommendation model.
    
    Returns:
        ModelStatusResponse with model information.
    
    Raises:
        HTTPException: If status retrieval fails.
    """
    try:
        recommender = get_recommender()
        
        return ModelStatusResponse(
            available=recommender.is_available(),
            model_version=recommender.model_version,
            model_path=str(recommender.model_path) if recommender.model_path else None
        )
        
    except Exception as e:
        logger.error(f'Error getting model status: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get model status'
        )

"""API routes for ML-based part recommendations."""

from typing import Dict, Any, Tuple
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.ml_model.recommender import MLRecommender
from app.models import Part
from app.exceptions import ValidationError

bp = Blueprint('recommendations', __name__)
logger = logging.getLogger(__name__)

_recommender: MLRecommender = None


def get_recommender() -> MLRecommender:
    """Get or create the ML recommender instance.
    
    Returns:
        MLRecommender instance.
    """
    global _recommender
    if _recommender is None:
        _recommender = MLRecommender()
    return _recommender


@bp.route('/parts', methods=['POST'])
@jwt_required()
def recommend_parts() -> Tuple[Dict[str, Any], int]:
    """Get ML-based part recommendations.
    
    Request Body:
        part_type: Type of part to recommend (optional).
        budget: Budget constraint in USD (required).
        existing_parts: Array of part IDs already selected (optional).
        min_performance: Minimum performance score 0-10 (optional, default: 5).
        num_recommendations: Number of recommendations (optional, default: 10).
    
    Returns:
        JSON response with recommended parts and scores.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        budget = data.get('budget')
        if budget is None:
            return jsonify({'error': 'Budget is required'}), 400
        
        try:
            budget = float(budget)
            if budget <= 0:
                raise ValueError('Budget must be positive')
        except (ValueError, TypeError):
            return jsonify({'error': 'Budget must be a positive number'}), 400
        
        user_preferences = {
            'part_type': data.get('part_type'),
            'budget': budget,
            'min_performance': data.get('min_performance', 5),
            'budget_ratio': data.get('budget_ratio', 0.3)
        }
        
        existing_parts = data.get('existing_parts', [])
        if not isinstance(existing_parts, list):
            return jsonify({'error': 'existing_parts must be an array'}), 400
        
        # Verify existing parts belong to user
        if existing_parts:
            user_parts = Part.query.filter(
                Part.id.in_(existing_parts),
                Part.user_id == user_id
            ).all()
            if len(user_parts) != len(existing_parts):
                return jsonify({'error': 'Some existing parts not found or not owned by you'}), 403
        
        num_recommendations = data.get('num_recommendations', 10)
        try:
            num_recommendations = int(num_recommendations)
            if num_recommendations < 1 or num_recommendations > 50:
                raise ValueError('num_recommendations must be between 1 and 50')
        except (ValueError, TypeError):
            return jsonify({'error': 'num_recommendations must be an integer between 1 and 50'}), 400
        
        # Get recommendations (filtered by user's parts)
        recommender = get_recommender()
        recommendations = recommender.recommend_parts(
            user_preferences=user_preferences,
            budget=budget,
            existing_parts=existing_parts if existing_parts else None,
            num_recommendations=num_recommendations,
            user_id=user_id  # Filter by user
        )
        
        return jsonify({
            'recommendations': recommendations,
            'count': len(recommendations),
            'model_version': recommender.model_version if recommender.is_available() else 'rule-based'
        }), 200
        
    except Exception as e:
        logger.error(f'Error generating recommendations: {e}', exc_info=True)
        return jsonify({'error': 'Failed to generate recommendations'}), 500


@bp.route('/model/status', methods=['GET'])
def model_status() -> Tuple[Dict[str, Any], int]:
    """Get status of the ML recommendation model.
    
    Returns:
        JSON response with model status information.
    """
    try:
        recommender = get_recommender()
        
        return jsonify({
            'available': recommender.is_available(),
            'model_version': recommender.model_version,
            'model_path': str(recommender.model_path) if recommender.model_path else None
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting model status: {e}', exc_info=True)
        return jsonify({'error': 'Failed to get model status'}), 500


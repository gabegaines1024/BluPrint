"""Machine learning-based PC part recommendation system."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.models import Part
from app.database import db

logger = logging.getLogger(__name__)


class MLRecommender:
    """Machine learning-based recommender for PC parts.
    
    This class handles loading trained models and generating recommendations
    based on user preferences and existing build patterns.
    
    Attributes:
        model: Trained scikit-learn model pipeline.
        model_version: Version of the loaded model.
        model_path: Path to the model file.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ML recommender.
        
        Args:
            model_path: Path to the saved model file. If None, uses default path.
        """
        if model_path is None:
            base_dir = Path(__file__).parent
            model_path = base_dir / 'models' / 'recommender_model_v1.pkl'
        
        self.model_path = Path(model_path)
        self.model: Optional[Pipeline] = None
        self.model_version: str = 'unknown'
        self.feature_names: List[str] = []
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model from disk.
        
        Raises:
            FileNotFoundError: If model file doesn't exist.
            ValueError: If model file is corrupted.
        """
        if not self.model_path.exists():
            logger.warning(f'Model file not found at {self.model_path}. '
                         'Recommendations will be unavailable.')
            return
        
        try:
            model_data = joblib.load(self.model_path)
            
            if isinstance(model_data, dict):
                self.model = model_data.get('model')
                self.model_version = model_data.get('version', 'unknown')
                self.feature_names = model_data.get('feature_names', [])
            else:
                # Legacy format: just the model
                self.model = model_data
                self.model_version = 'legacy'
            
            logger.info(f'Loaded ML model version {self.model_version} from {self.model_path}')
            
        except Exception as e:
            logger.error(f'Error loading model: {e}', exc_info=True)
            raise ValueError(f'Failed to load model: {e}')
    
    def is_available(self) -> bool:
        """Check if the model is loaded and available.
        
        Returns:
            True if model is loaded, False otherwise.
        """
        return self.model is not None
    
    def recommend_parts(self, 
                       user_preferences: Dict[str, Any],
                       budget: float,
                       existing_parts: Optional[List[int]] = None,
                       num_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Generate part recommendations based on user preferences.
        
        Args:
            user_preferences: Dictionary with user preferences (e.g., 
                            {'part_type': 'GPU', 'min_performance': 8}).
            budget: Budget constraint in USD.
            existing_parts: List of part IDs already selected (for compatibility).
            num_recommendations: Number of recommendations to return.
        
        Returns:
            List of recommended parts with scores.
        
        Raises:
            RuntimeError: If model is not loaded.
        """
        if not self.is_available():
            logger.warning('Model not available, falling back to rule-based recommendations')
            return self._fallback_recommendations(user_preferences, budget, existing_parts, num_recommendations)
        
        try:
            # Get candidate parts
            candidates = self._get_candidate_parts(user_preferences, budget, existing_parts)
            
            if not candidates:
                return []
            
            # Extract features for candidates
            features_df = self._extract_features(candidates, user_preferences)
            
            # Ensure feature order matches training
            if self.feature_names:
                # Add missing columns with 0
                missing_cols = set(self.feature_names) - set(features_df.columns)
                for col in missing_cols:
                    features_df[col] = 0
                # Reorder to match training
                features_df = features_df[self.feature_names]
            
            # Generate predictions (relevance scores)
            scores = self.model.predict(features_df.values)
            
            # Combine parts with scores
            recommendations = [
                {
                    'part': part.to_dict(),
                    'score': float(score),
                    'reason': self._generate_reason(part, score, user_preferences)
                }
                for part, score in zip(candidates, scores)
            ]
            
            # Sort by score (descending) and limit
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f'Error generating recommendations: {e}', exc_info=True)
            return self._fallback_recommendations(user_preferences, budget, existing_parts, num_recommendations)
    
    def _get_candidate_parts(self, 
                            user_preferences: Dict[str, Any],
                            budget: float,
                            existing_parts: Optional[List[int]]) -> List[Part]:
        """Get candidate parts matching user preferences.
        
        Args:
            user_preferences: User preference dictionary.
            budget: Budget constraint.
            existing_parts: Already selected parts.
        
        Returns:
            List of candidate Part objects.
        """
        query = Part.query.filter(Part.price.isnot(None), Part.price > 0)
        
        # Filter by part type if specified
        part_type = user_preferences.get('part_type')
        if part_type:
            query = query.filter(Part.part_type == part_type)
        
        # Budget filter
        query = query.filter(Part.price <= budget)
        
        # Exclude existing parts
        if existing_parts:
            query = query.filter(~Part.id.in_(existing_parts))
        
        return query.limit(100).all()  # Limit candidates for performance
    
    def _extract_features(self, 
                         parts: List[Part],
                         user_preferences: Dict[str, Any]) -> pd.DataFrame:
        """Extract features from parts for model prediction.
        
        Args:
            parts: List of Part objects.
            user_preferences: User preferences dictionary.
        
        Returns:
            DataFrame with extracted features.
        """
        features = []
        
        for part in parts:
            feature_dict = {
                'price': part.price or 0.0,
                'part_type_encoded': self._encode_part_type(part.part_type),
                'has_manufacturer': 1.0 if part.manufacturer else 0.0,
            }
            
            # Extract numeric features from specifications
            specs = part.specifications or {}
            
            # Common specification features
            feature_dict['power_consumption'] = float(specs.get('power_consumption', 0))
            feature_dict['memory_size'] = float(specs.get('memory_size', 0))
            feature_dict['core_count'] = float(specs.get('core_count', 0))
            feature_dict['clock_speed'] = float(specs.get('clock_speed', 0))
            feature_dict['storage_capacity'] = float(specs.get('storage_capacity', 0))
            
            # User preference alignment
            preferred_performance = user_preferences.get('min_performance', 5)
            feature_dict['performance_score'] = self._estimate_performance(part, specs)
            feature_dict['performance_match'] = 1.0 if feature_dict['performance_score'] >= preferred_performance else 0.0
            
            preferred_budget_ratio = user_preferences.get('budget_ratio', 0.5)
            user_budget = user_preferences.get('budget', 1000)
            feature_dict['budget_alignment'] = abs((part.price or 0) / (user_budget + 1) - preferred_budget_ratio)
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def _encode_part_type(self, part_type: str) -> float:
        """Encode part type as numeric value.
        
        Args:
            part_type: Part type string.
        
        Returns:
            Encoded numeric value.
        """
        encoding_map = {
            'CPU': 1.0, 'GPU': 2.0, 'RAM': 3.0, 'Motherboard': 4.0,
            'Storage': 5.0, 'PSU': 6.0, 'Case': 7.0, 'Cooler': 8.0,
            'Network': 9.0, 'Other': 10.0
        }
        return encoding_map.get(part_type, 0.0)
    
    def _estimate_performance(self, part: Part, specs: Dict[str, Any]) -> float:
        """Estimate performance score for a part (0-10 scale).
        
        Args:
            part: Part object.
            specs: Part specifications dictionary.
        
        Returns:
            Performance score (0-10).
        """
        # Simple heuristic-based performance estimation
        # In production, this could be more sophisticated
        
        if part.part_type == 'CPU':
            core_count = specs.get('core_count', 4)
            clock_speed = specs.get('clock_speed', 2.0)
            return min(10.0, (core_count * clock_speed) / 5.0)
        
        elif part.part_type == 'GPU':
            memory = specs.get('memory_size', 4)
            clock_speed = specs.get('clock_speed', 1.0)
            return min(10.0, (memory * clock_speed) / 2.0)
        
        elif part.part_type == 'RAM':
            size = specs.get('memory_size', 8)
            speed = specs.get('clock_speed', 2400)
            return min(10.0, (size * speed) / 3000.0)
        
        # Default: based on price (rough heuristic)
        price = part.price or 0
        return min(10.0, price / 200.0)
    
    def _generate_reason(self, 
                        part: Part,
                        score: float,
                        user_preferences: Dict[str, Any]) -> str:
        """Generate human-readable reason for recommendation.
        
        Args:
            part: Recommended part.
            score: Recommendation score.
            user_preferences: User preferences.
        
        Returns:
            Reason string.
        """
        reasons = []
        
        if score > 8.0:
            reasons.append("High compatibility match")
        
        if part.price and part.price <= user_preferences.get('budget', 1000) * 0.8:
            reasons.append("Good value for budget")
        
        perf_score = self._estimate_performance(part, part.specifications or {})
        if perf_score >= user_preferences.get('min_performance', 5):
            reasons.append("Meets performance requirements")
        
        if not reasons:
            reasons.append("Good overall match")
        
        return "; ".join(reasons)
    
    def _fallback_recommendations(self,
                                 user_preferences: Dict[str, Any],
                                 budget: float,
                                 existing_parts: Optional[List[int]],
                                 num_recommendations: int) -> List[Dict[str, Any]]:
        """Fallback to rule-based recommendations when ML model unavailable.
        
        Args:
            user_preferences: User preferences.
            budget: Budget constraint.
            existing_parts: Already selected parts.
            num_recommendations: Number of recommendations.
        
        Returns:
            List of fallback recommendations.
        """
        try:
            from app.services.recommender_v1 import RuleBasedRecommender
            
            recommender = RuleBasedRecommender()
            return recommender.recommend(
                part_type=user_preferences.get('part_type'),
                budget=budget,
                existing_parts=existing_parts,
                limit=num_recommendations
            )
        except Exception as e:
            logger.error(f'Fallback recommender failed: {e}')
            return []


"""Rule-based recommender as fallback when ML model is unavailable."""

from typing import List, Dict, Any, Optional
from app.models import Part


class RuleBasedRecommender:
    """Simple rule-based recommender for PC parts.
    
    This provides baseline recommendations using heuristics when
    the ML model is not available or for simple queries.
    """
    
    def recommend(self,
                 part_type: Optional[str] = None,
                 budget: float = 1000.0,
                 existing_parts: Optional[List[int]] = None,
                 limit: int = 10) -> List[Dict[str, Any]]:
        """Generate rule-based recommendations.
        
        Args:
            part_type: Type of part to recommend.
            budget: Budget constraint.
            existing_parts: Already selected part IDs.
            limit: Maximum number of recommendations.
        
        Returns:
            List of recommended parts with basic scoring.
        """
        query = Part.query.filter(Part.price.isnot(None), Part.price > 0)
        
        if part_type:
            query = query.filter(Part.part_type == part_type)
        
        query = query.filter(Part.price <= budget)
        
        if existing_parts:
            query = query.filter(~Part.id.in_(existing_parts))
        
        parts = query.order_by(Part.price.asc()).limit(limit * 2).all()
        
        # Score by value (price efficiency)
        recommendations = []
        for part in parts:
            score = self._calculate_value_score(part, budget)
            recommendations.append({
                'part': part.to_dict(),
                'score': score,
                'reason': f'Good value within budget (${part.price})'
            })
        
        # Sort by score and return top N
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    def _calculate_value_score(self, part: Part, budget: float) -> float:
        """Calculate value score for a part.
        
        Args:
            part: Part to score.
            budget: Total budget.
        
        Returns:
            Value score (0-10).
        """
        if not part.price or part.price <= 0:
            return 0.0
        
        # Prefer mid-range parts (not too cheap, not too expensive)
        budget_ratio = part.price / budget if budget > 0 else 0
        
        if 0.1 <= budget_ratio <= 0.3:
            return 8.0
        elif 0.3 < budget_ratio <= 0.5:
            return 7.0
        elif 0.5 < budget_ratio <= 0.7:
            return 6.0
        else:
            return 5.0


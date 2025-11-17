"""Machine learning module for PC build recommendations."""

from app.ml_model.recommender import MLRecommender
from app.ml_model.train_model import train_recommendation_model

__all__ = ['MLRecommender', 'train_recommendation_model']


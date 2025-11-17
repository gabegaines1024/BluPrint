#!/usr/bin/env python3
"""Script to train the ML recommendation model."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ml_model.train_model import train_recommendation_model

if __name__ == '__main__':
    print("=" * 60)
    print("Training PC Part Recommendation Model")
    print("=" * 60)
    print()
    
    try:
        metrics = train_recommendation_model('v1')
        
        print("\n" + "=" * 60)
        print("Training Complete!")
        print("=" * 60)
        print(f"\nModel Performance Metrics:")
        print(f"  Test R² Score: {metrics['test_r2']:.3f}")
        print(f"  Test RMSE: {metrics['test_rmse']:.3f}")
        print(f"  Cross-Validation R²: {metrics['cv_r2_mean']:.3f} ± {metrics['cv_r2_std']:.3f}")
        print(f"\nModel Details:")
        print(f"  Version: {metrics['model_version']}")
        print(f"  Training Date: {metrics['training_date']}")
        print(f"  Samples: {metrics['n_samples']}")
        print(f"  Features: {metrics['n_features']}")
        print(f"\nModel saved to: app/ml_model/models/recommender_model_v1.pkl")
        print("\nYou can now use the recommendation API!")
        
    except Exception as e:
        print(f"\nError training model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


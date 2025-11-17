"""Script for training the PC part recommendation model."""

import logging
from pathlib import Path
from typing import Tuple
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _encode_part_type(part_type: str) -> float:
    """Encode part type as numeric value."""
    encoding_map = {
        'CPU': 1.0, 'GPU': 2.0, 'RAM': 3.0, 'Motherboard': 4.0,
        'Storage': 5.0, 'PSU': 6.0, 'Case': 7.0, 'Cooler': 8.0,
        'Network': 9.0, 'Other': 10.0
    }
    return encoding_map.get(part_type, 0.0)


def _generate_synthetic_data(num_samples: int = 1000) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic training data when no real data is available.
    
    Args:
        num_samples: Number of synthetic samples to generate.
    
    Returns:
        Tuple of (features DataFrame, target Series).
    """
    np.random.seed(42)
    
    features = {
        'price': np.random.uniform(50, 2000, num_samples),
        'part_type_encoded': np.random.choice([1, 2, 3, 4, 5, 6], num_samples),
        'has_manufacturer': np.random.choice([0, 1], num_samples),
        'power_consumption': np.random.uniform(0, 500, num_samples),
        'memory_size': np.random.uniform(0, 64, num_samples),
        'core_count': np.random.uniform(0, 16, num_samples),
        'clock_speed': np.random.uniform(0, 5, num_samples),
        'storage_capacity': np.random.uniform(0, 2000, num_samples),
        'performance_score': np.random.uniform(0, 10, num_samples),
        'performance_match': np.random.choice([0, 1], num_samples),
        'budget_alignment': np.random.uniform(0, 1, num_samples),
    }
    
    # Generate synthetic targets based on features
    targets = (
        features['performance_match'] * 5.0 +
        (features['price'] < 500).astype(float) * 2.0 +
        np.random.normal(0, 0.5, num_samples)
    )
    targets = np.clip(targets, 0, 10)
    
    return pd.DataFrame(features), pd.Series(targets)


def load_training_data():
    """Load training data from database or generate synthetic data.
    
    Returns:
        Tuple of (features DataFrame, target Series).
    """
    try:
        # Try to import Flask app components
        try:
            from app import create_app
            from app.database import db
            from app.models import Part, Build
        except ImportError:
            logger.warning('Flask app not available, using synthetic data')
            return _generate_synthetic_data()
        
        app = create_app('development')
        
        with app.app_context():
            builds = Build.query.filter(Build.parts.isnot(None)).all()
            
            features_list = []
            targets_list = []
            
            for build in builds:
                if not build.parts or len(build.parts) == 0:
                    continue
                
                parts = Part.query.filter(Part.id.in_(build.parts)).all()
                
                if not parts:
                    continue
                
                # Calculate target: normalized score based on build properties
                # Higher score = better build (compatible, reasonable price)
                target_score = 0.0
                if build.is_compatible:
                    target_score += 5.0
                
                # Price efficiency (lower price per part = better)
                avg_price = build.total_price / len(parts) if build.total_price and len(parts) > 0 else 0
                if 0 < avg_price < 500:
                    target_score += 3.0
                elif avg_price < 1000:
                    target_score += 2.0
                
                # Build completeness (more parts = more complete)
                unique_types = len(set(p.part_type for p in parts))
                target_score += min(2.0, unique_types / 5.0)
                
                # Normalize to 0-10 scale
                target_score = min(10.0, target_score)
                
                # Extract features for each part in the build
                for part in parts:
                    specs = part.specifications or {}
                    
                    # Calculate performance score
                    perf_score = 0.0
                    if part.part_type == 'CPU':
                        core_count = specs.get('core_count', 4)
                        clock_speed = specs.get('clock_speed', 2.0)
                        perf_score = min(10.0, (core_count * clock_speed) / 5.0)
                    elif part.part_type == 'GPU':
                        memory = specs.get('memory_size', 4)
                        clock_speed = specs.get('clock_speed', 1.0)
                        perf_score = min(10.0, (memory * clock_speed) / 2.0)
                    else:
                        price = part.price or 0
                        perf_score = min(10.0, price / 200.0)
                    
                    features = {
                        'price': float(part.price or 0),
                        'part_type_encoded': _encode_part_type(part.part_type),
                        'has_manufacturer': 1.0 if part.manufacturer else 0.0,
                        'power_consumption': float(specs.get('power_consumption', 0)),
                        'memory_size': float(specs.get('memory_size', 0)),
                        'core_count': float(specs.get('core_count', 0)),
                        'clock_speed': float(specs.get('clock_speed', 0)),
                        'storage_capacity': float(specs.get('storage_capacity', 0)),
                        'performance_score': perf_score,
                        'performance_match': 1.0 if perf_score >= 5 else 0.0,
                        'budget_alignment': abs((part.price or 0) / (build.total_price or 1000 + 1) - 0.3),
                    }
                    features_list.append(features)
                    targets_list.append(target_score)
            
            if not features_list:
                logger.warning('No training data found. Using synthetic data.')
                return _generate_synthetic_data()
            
            return pd.DataFrame(features_list), pd.Series(targets_list)
            
    except Exception as e:
        logger.warning(f'Error loading from database: {e}. Using synthetic data.')
        return _generate_synthetic_data()


def train_recommendation_model(model_version: str = 'v1'):
    """Train the recommendation model.
    
    Args:
        model_version: Version identifier for the model.
    
    Returns:
        Dictionary with training metrics and model information.
    """
    logger.info('Starting model training...')
    
    # Load training data
    X, y = load_training_data()
    
    # Handle missing values
    X = X.fillna(0)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    # Train model
    logger.info('Training model...')
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    train_pred = pipeline.predict(X_train)
    test_pred = pipeline.predict(X_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='r2')
    
    metrics = {
        'train_rmse': float(train_rmse),
        'test_rmse': float(test_rmse),
        'train_r2': float(train_r2),
        'test_r2': float(test_r2),
        'cv_r2_mean': float(cv_scores.mean()),
        'cv_r2_std': float(cv_scores.std()),
        'model_version': model_version,
        'training_date': datetime.now().isoformat(),
        'feature_names': list(X.columns),
        'n_samples': len(X),
        'n_features': len(X.columns)
    }
    
    logger.info(f'Training completed. Test R²: {test_r2:.3f}, Test RMSE: {test_rmse:.3f}')
    
    # Save model
    model_dir = Path(__file__).parent / 'models'
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / f'recommender_model_{model_version}.pkl'
    
    model_data = {
        'model': pipeline,
        'version': model_version,
        'feature_names': list(X.columns),
        'metrics': metrics,
        'trained_at': datetime.now().isoformat()
    }
    
    joblib.dump(model_data, model_path)
    logger.info(f'Model saved to {model_path}')
    
    return metrics


if __name__ == '__main__':
    """Run model training from command line."""
    metrics = train_recommendation_model('v1')
    print("\nTraining Metrics:")
    print(f"  Test R² Score: {metrics['test_r2']:.3f}")
    print(f"  Test RMSE: {metrics['test_rmse']:.3f}")
    print(f"  CV R² Mean: {metrics['cv_r2_mean']:.3f} ± {metrics['cv_r2_std']:.3f}")


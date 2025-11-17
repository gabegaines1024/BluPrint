# ML Recommendation System - Setup Guide

## ✅ **What's Been Implemented**

### **1. ML Model Training Pipeline** (`app/ml_model/train_model.py`)
- ✅ Complete training script with scikit-learn
- ✅ Uses RandomForestRegressor for recommendations
- ✅ Feature engineering from part specifications
- ✅ Model evaluation with cross-validation
- ✅ Model persistence with joblib
- ✅ Falls back to synthetic data if no database data available

### **2. ML Recommender Service** (`app/ml_model/recommender.py`)
- ✅ MLRecommender class for loading and using trained models
- ✅ Feature extraction from parts
- ✅ Performance estimation heuristics
- ✅ Fallback to rule-based recommendations when model unavailable
- ✅ Handles missing models gracefully

### **3. Rule-Based Fallback** (`app/services/recommender_v1.py`)
- ✅ Simple heuristic-based recommender
- ✅ Value scoring based on budget ratios
- ✅ Used when ML model is not available

### **4. Recommendation API** (`app/routes/recommendations.py`)
- ✅ `POST /api/v1/recommendations/parts` - Get ML recommendations
- ✅ `GET /api/v1/recommendations/model/status` - Check model status
- ✅ Full input validation
- ✅ Error handling

### **5. Integration**
- ✅ Routes registered in app factory
- ✅ Dependencies added to requirements.txt
- ✅ Model directory structure created

---

## 🚀 **How to Use**

### **Step 1: Train the Model**

**Option A: Using the standalone script (Recommended)**
```bash
# Make sure you're in the project directory and virtual environment is activated
python train_ml_model.py
```

**Option B: Using Python module**
```bash
python -m app.ml_model.train_model
```

**What happens:**
- The script will try to load training data from your database (existing builds)
- If no data exists, it generates synthetic training data
- Trains a RandomForest model
- Saves the model to `app/ml_model/models/recommender_model_v1.pkl`
- Prints training metrics

### **Step 2: Use the Recommendations API**

**Check model status:**
```bash
curl http://localhost:5000/api/v1/recommendations/model/status
```

**Get recommendations:**
```bash
curl -X POST http://localhost:5000/api/v1/recommendations/parts \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 500,
    "part_type": "GPU",
    "num_recommendations": 5
  }'
```

**Example response:**
```json
{
  "recommendations": [
    {
      "part": {
        "id": 1,
        "name": "NVIDIA RTX 3060",
        "part_type": "GPU",
        "price": 329.99,
        ...
      },
      "score": 8.5,
      "reason": "High compatibility match; Good value for budget"
    },
    ...
  ],
  "count": 5,
  "model_version": "v1"
}
```

---

## 📊 **How It Works**

### **Feature Engineering**
The model uses these features:
- `price` - Part price
- `part_type_encoded` - Encoded part type (CPU=1, GPU=2, etc.)
- `has_manufacturer` - Whether manufacturer is specified
- `power_consumption` - From specifications
- `memory_size` - From specifications
- `core_count` - From specifications
- `clock_speed` - From specifications
- `storage_capacity` - From specifications
- `performance_score` - Estimated performance (0-10)
- `performance_match` - Whether meets user's min_performance
- `budget_alignment` - How well price fits budget

### **Model Architecture**
- **Algorithm:** RandomForestRegressor
- **Pipeline:** StandardScaler → RandomForestRegressor
- **Target:** Relevance score (0-10) for part recommendations
- **Training:** Uses existing builds to learn what makes good part combinations

### **Recommendation Process**
1. User provides preferences (budget, part type, etc.)
2. System fetches candidate parts matching criteria
3. Extracts features from each candidate part
4. Model predicts relevance score for each part
5. Parts sorted by score and top N returned
6. If model unavailable, falls back to rule-based recommendations

---

## 🔧 **Configuration**

### **Model Parameters** (in `train_model.py`)
```python
RandomForestRegressor(
    n_estimators=100,    # Number of trees
    max_depth=10,        # Max tree depth
    random_state=42,     # For reproducibility
    n_jobs=-1            # Use all CPU cores
)
```

### **Model Location**
- Default: `app/ml_model/models/recommender_model_v1.pkl`
- Can be changed in `MLRecommender.__init__()`

---

## 📈 **Improving the Model**

### **1. Add More Training Data**
- Create more builds in the system
- The model learns from build patterns
- More diverse builds = better recommendations

### **2. Feature Engineering**
Add more features in `_extract_features()`:
- User preferences
- Part popularity
- Brand preferences
- Historical compatibility data

### **3. Model Tuning**
Adjust hyperparameters in `train_model.py`:
- Try different algorithms (GradientBoosting, XGBoost)
- Tune n_estimators, max_depth
- Use GridSearchCV for optimization

### **4. Evaluation Metrics**
Current metrics:
- R² Score (coefficient of determination)
- RMSE (Root Mean Squared Error)
- Cross-validation scores

---

## 🐛 **Troubleshooting**

### **Model Not Found Error**
- **Solution:** Run `python train_ml_model.py` to create the model
- The system will use rule-based recommendations until model is trained

### **Poor Recommendations**
- **Solution:** Add more training data (create more builds)
- Or adjust feature engineering
- Or retrain with different parameters

### **Import Errors**
- **Solution:** Make sure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`

---

## 📝 **API Documentation**

### **POST /api/v1/recommendations/parts**

**Request Body:**
```json
{
  "budget": 1000,              // Required: Budget in USD
  "part_type": "GPU",          // Optional: Filter by part type
  "existing_parts": [1, 2],    // Optional: Already selected part IDs
  "min_performance": 7,        // Optional: Min performance score (0-10)
  "num_recommendations": 10    // Optional: Number of recommendations (1-50)
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "part": { /* part object */ },
      "score": 8.5,
      "reason": "High compatibility match; Good value for budget"
    }
  ],
  "count": 10,
  "model_version": "v1"
}
```

### **GET /api/v1/recommendations/model/status**

**Response:**
```json
{
  "available": true,
  "model_version": "v1",
  "model_path": "app/ml_model/models/recommender_model_v1.pkl"
}
```

---

## ✅ **Status**

- ✅ ML training pipeline: **Complete**
- ✅ Recommendation service: **Complete**
- ✅ API endpoints: **Complete**
- ✅ Fallback system: **Complete**
- ✅ Integration: **Complete**

**The ML recommendation system is fully implemented and ready to use!**


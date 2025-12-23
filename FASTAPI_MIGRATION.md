# FastAPI Migration Guide

## Overview

Your BluPrint application has been successfully migrated from Flask to FastAPI! This document provides information on what's changed and how to run the new application.

## What's New

### 🚀 Performance Improvements
- **FastAPI** - Modern, high-performance web framework
- **Async capabilities** - Ready for async/await operations
- **Automatic data validation** with Pydantic
- **Type safety** throughout the codebase

### 📚 Automatic API Documentation
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## Key Changes

### 1. Dependencies
Updated `requirements.txt` with FastAPI ecosystem:
- `fastapi` - Core framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-jose` - JWT authentication
- `passlib` - Password hashing

### 2. Project Structure
```
app/
├── main.py                  # FastAPI app initialization (NEW)
├── schemas.py               # Pydantic models (NEW)
├── dependencies.py          # Auth dependencies (NEW)
├── models.py                # SQLAlchemy models (UPDATED)
├── database.py              # Database setup (UPDATED)
├── cache.py                 # Caching (UPDATED)
├── routes/                  # All routes converted to FastAPI
│   ├── auth.py
│   ├── parts.py
│   ├── compatibility.py
│   ├── builds.py
│   ├── recommendations.py
│   └── agent.py
├── services/
│   └── auth_service.py      # Updated for FastAPI
└── ...
main.py                       # Application entry point (NEW)
```

### 3. Database
- Migrated from Flask-SQLAlchemy to pure SQLAlchemy 2.0
- Session management via dependency injection
- Backward compatible with existing SQLite database

### 4. Authentication
- JWT tokens using `python-jose` instead of Flask-JWT-Extended
- Bearer token authentication
- Same token format, just different implementation

### 5. API Endpoints
All endpoints remain the same:
- `/api/v1/auth/*` - Authentication
- `/api/v1/parts/*` - Parts management
- `/api/v1/compatibility/*` - Compatibility checking
- `/api/v1/builds/*` - Builds management
- `/api/v1/recommendations/*` - ML recommendations
- `/api/v1/agent/*` - AI agent

## Installation

### 1. Install New Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Same as before, but with optional FastAPI-specific settings:

```bash
# Required
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=sqlite:///./instance/bluprint.db

# Server (optional)
HOST=0.0.0.0
PORT=8000
RELOAD=true  # Auto-reload on code changes

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log

# CORS
CORS_ORIGINS=*
```

## Running the Application

### Development Mode
```bash
# Method 1: Using main.py
python main.py

# Method 2: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Method 3: With specific config
HOST=0.0.0.0 PORT=8000 RELOAD=true python main.py
```

### Production Mode
```bash
# Basic production run
uvicorn app.main:app --host 0.0.0.0 --port 8000

# With workers for better performance
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn + Uvicorn workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

### Update Test Configuration
Your tests need to be updated for FastAPI. Install:
```bash
pip install pytest pytest-asyncio httpx
```

Example test with FastAPI TestClient:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## API Documentation

Once the server is running, access interactive documentation:

1. **Swagger UI** (recommended): http://localhost:8000/api/docs
   - Try out endpoints directly
   - See request/response schemas
   - Test authentication

2. **ReDoc**: http://localhost:8000/api/redoc
   - Alternative documentation view
   - Better for reading/reference

## Migration Notes

### What Still Works
✅ Existing database (no migration needed)
✅ All API endpoints (same paths)
✅ JWT tokens (compatible format)
✅ Frontend (no changes needed)
✅ Caching system
✅ ML model integration

### What's Improved
✨ Automatic request validation
✨ Better error messages
✨ Type hints everywhere
✨ Faster performance
✨ Built-in API docs
✨ Better async support

### What to Update

1. **Old Flask Test Files**: Update to use FastAPI TestClient
2. **Docker/Deployment**: Update commands to use `uvicorn` instead of `flask run`
3. **Monitoring**: Update health check endpoints if needed

## Common Issues

### Issue: Import errors
**Solution**: Make sure all new dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Database connection errors
**Solution**: Ensure DATABASE_URL is set correctly and instance directory exists:
```bash
mkdir -p instance
```

### Issue: Authentication not working
**Solution**: Verify SECRET_KEY and JWT_SECRET_KEY are set in environment

### Issue: CORS errors from frontend
**Solution**: Set CORS_ORIGINS environment variable:
```bash
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

## Performance Comparison

Expected improvements:
- **Request handling**: 2-3x faster
- **JSON serialization**: Built-in optimization
- **Validation**: Automatic with Pydantic (faster than manual checks)
- **Async ready**: Can leverage async DB operations in future

## Next Steps

1. ✅ Run the application and test all endpoints
2. ✅ Check the auto-generated API documentation
3. ✅ Update your frontend client if needed (same endpoints)
4. ✅ Update tests to use FastAPI TestClient
5. ✅ Deploy with uvicorn instead of gunicorn+flask

## Support

For issues or questions:
1. Check FastAPI documentation: https://fastapi.tiangolo.com
2. Review this migration guide
3. Check application logs in `app.log`

## Rollback (if needed)

If you need to rollback to Flask:
```bash
git checkout HEAD~1  # Go back to previous commit
pip install -r requirements.txt  # Reinstall old dependencies
python run.py  # Run old Flask app
```

---

**🎉 Congratulations!** Your BluPrint API is now powered by FastAPI!


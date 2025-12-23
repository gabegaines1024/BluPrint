# Quick Fix for ModuleNotFoundError

## The Problem
The error `ModuleNotFoundError: No module named 'flask_jwt_extended'` is happening because:
1. You're still using Python 3.14's `.venv` (in `app/.venv`)
2. Python cached the old Flask version of `app/__init__.py`
3. The app is trying to use multiple workers which multiplies the problem

## The Solution

Run these commands in order:

```bash
cd /Users/gabegaines/workflow/python_proj/BluPrint

# 1. STOP the current server (Ctrl+C if running)

# 2. Deactivate current venv
deactivate

# 3. Remove the problematic Python 3.14 venv
rm -rf app/.venv

# 4. Remove ALL Python cache
find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf
find . -name "*.pyc" -delete

# 5. Create NEW venv with Python 3.12 in the root
python3.12 -m venv venv

# 6. Activate it
source venv/bin/activate

# 7. Verify you're using 3.12
python --version  # Should show Python 3.12.x

# 8. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 9. Run WITHOUT multiple workers (simpler, no multiprocessing)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the simple Python runner
python main.py
```

## Alternative: Quick One-Liner

```bash
cd /Users/gabegaines/workflow/python_proj/BluPrint && deactivate; rm -rf app/.venv; find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main.py
```

## Why This Happens

- **Python 3.14** is too new - pydantic-core doesn't support it yet
- **Python bytecode cache** (`.pyc` files) stores the old Flask imports
- **Multiple workers** (`--workers 4`) means 4 processes all failing at once

## After It Works

Once the server starts successfully:
- Visit: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs
- You can then safely delete `old_flask_backup/`


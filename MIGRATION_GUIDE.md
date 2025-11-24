# Migration Guide - Adding Authentication

This guide explains how to migrate your existing database to support the new authentication system.

## Database Migration

The new authentication system adds:
- `users` table
- `user_id` column to `parts` table
- `user_id` column to `builds` table

### Step 1: Create Migration

Run the following command to create a new migration:

```bash
flask db migrate -m "Add user authentication and ownership"
```

### Step 2: Review Migration

Review the generated migration file in `migrations/versions/` to ensure it looks correct.

### Step 3: Apply Migration

```bash
flask db upgrade
```

## Data Migration (If you have existing data)

If you have existing parts or builds in your database, you'll need to:

1. Create a default admin user
2. Assign existing parts/builds to that user

You can do this with a Python script:

```python
from app import create_app
from app.database import db
from app.models import User, Part, Build

app = create_app()
with app.app_context():
    # Create default user
    admin = User(username='admin', email='admin@example.com')
    admin.set_password('changeme')
    db.session.add(admin)
    db.session.commit()
    
    # Assign existing parts to admin
    Part.query.update({Part.user_id: admin.id})
    
    # Assign existing builds to admin
    Build.query.update({Build.user_id: admin.id})
    
    db.session.commit()
```

## API Changes

### New Endpoints

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user (requires auth)
- `PUT /api/v1/auth/me` - Update current user (requires auth)

### Authentication Required

All existing endpoints now require authentication:
- All `/api/v1/parts/*` endpoints
- All `/api/v1/builds/*` endpoints
- `/api/v1/compatibility/check`
- `/api/v1/recommendations/parts`

### Request Headers

All authenticated requests require:
```
Authorization: Bearer <access_token>
```

## Frontend Updates Needed

1. Add login/register UI
2. Store JWT token in localStorage/sessionStorage
3. Include token in all API requests
4. Handle 401 errors (redirect to login)

## Testing

After migration, test:
1. User registration
2. User login
3. Creating parts (should be owned by logged-in user)
4. Creating builds (should only use user's parts)
5. Accessing other users' resources (should fail)


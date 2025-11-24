"""Pytest configuration and fixtures."""

import pytest
from app import create_app
from app.database import db
from app.models import User, Part, Build, CompatibilityRule
from flask_jwt_extended import create_access_token


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post('/api/v1/auth/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password': 'testpass123'
        }


@pytest.fixture
def test_part(app, test_user):
    """Create a test part."""
    with app.app_context():
        part = Part(
            user_id=test_user['id'],
            name='Test CPU',
            part_type='CPU',
            manufacturer='Test Manufacturer',
            price=299.99,
            specifications={
                'socket': 'AM4',
                'core_count': 6,
                'clock_speed': 3.5
            }
        )
        db.session.add(part)
        db.session.commit()
        return part


@pytest.fixture
def test_build(app, test_user, test_part):
    """Create a test build."""
    with app.app_context():
        build = Build(
            user_id=test_user['id'],
            name='Test Build',
            description='A test build',
            parts=[test_part.id],
            total_price=299.99,
            is_compatible=True,
            compatibility_issues=[]
        )
        db.session.add(build)
        db.session.commit()
        return build


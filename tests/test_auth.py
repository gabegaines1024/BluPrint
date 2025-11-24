"""Tests for authentication endpoints."""

import pytest


def test_register_user(client):
    """Test user registration."""
    response = client.post('/api/v1/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['username'] == 'newuser'


def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username."""
    response = client.post('/api/v1/auth/register', json={
        'username': test_user['username'],
        'email': 'different@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 400
    assert 'already exists' in response.get_json()['error'].lower()


def test_register_invalid_data(client):
    """Test registration with invalid data."""
    response = client.post('/api/v1/auth/register', json={
        'username': 'ab',  # Too short
        'email': 'invalid-email',
        'password': '123'  # Too short
    })
    
    assert response.status_code == 400


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post('/api/v1/auth/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == test_user['username']


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/api/v1/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get('/api/v1/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert 'username' in data['user']


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get('/api/v1/auth/me')
    
    assert response.status_code == 401


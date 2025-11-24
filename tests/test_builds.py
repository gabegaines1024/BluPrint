"""Tests for builds endpoints."""

import pytest


def test_get_builds_unauthorized(client):
    """Test getting builds without authentication."""
    response = client.get('/api/v1/builds')
    assert response.status_code == 401


def test_get_builds(client, auth_headers, test_build):
    """Test getting user's builds."""
    response = client.get('/api/v1/builds', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(build['id'] == test_build.id for build in data)


def test_create_build(client, auth_headers, test_part):
    """Test creating a build."""
    response = client.post('/api/v1/builds', headers=auth_headers, json={
        'name': 'New Build',
        'description': 'A new build',
        'parts': [test_part.id]
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Build'
    assert 'total_price' in data
    assert 'is_compatible' in data


def test_create_build_invalid_parts(client, auth_headers):
    """Test creating build with invalid part IDs."""
    response = client.post('/api/v1/builds', headers=auth_headers, json={
        'name': 'Invalid Build',
        'parts': [99999]  # Non-existent part
    })
    
    assert response.status_code == 400 or response.status_code == 404


def test_get_build(client, auth_headers, test_build):
    """Test getting a specific build."""
    response = client.get(f'/api/v1/builds/{test_build.id}', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == test_build.id


def test_update_build(client, auth_headers, test_build):
    """Test updating a build."""
    response = client.put(f'/api/v1/builds/{test_build.id}', headers=auth_headers, json={
        'name': 'Updated Build',
        'description': 'Updated description'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Build'


def test_delete_build(client, auth_headers, test_build):
    """Test deleting a build."""
    response = client.delete(f'/api/v1/builds/{test_build.id}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/api/v1/builds/{test_build.id}', headers=auth_headers)
    assert get_response.status_code == 404


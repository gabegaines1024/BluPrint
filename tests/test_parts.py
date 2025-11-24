"""Tests for parts endpoints."""

import pytest


def test_get_parts_unauthorized(client):
    """Test getting parts without authentication."""
    response = client.get('/api/v1/parts')
    assert response.status_code == 401


def test_get_parts(client, auth_headers, test_part):
    """Test getting user's parts."""
    response = client.get('/api/v1/parts', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(part['id'] == test_part.id for part in data)


def test_create_part(client, auth_headers):
    """Test creating a part."""
    response = client.post('/api/v1/parts', headers=auth_headers, json={
        'name': 'New GPU',
        'part_type': 'GPU',
        'manufacturer': 'NVIDIA',
        'price': 499.99,
        'specifications': {
            'memory_size': 8,
            'clock_speed': 1.5
        }
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New GPU'
    assert data['part_type'] == 'GPU'


def test_create_part_invalid_specs(client, auth_headers):
    """Test creating part with invalid specifications."""
    response = client.post('/api/v1/parts', headers=auth_headers, json={
        'name': 'Invalid CPU',
        'part_type': 'CPU',
        'specifications': {
            'core_count': -5  # Invalid: negative
        }
    })
    
    assert response.status_code == 400


def test_get_part(client, auth_headers, test_part):
    """Test getting a specific part."""
    response = client.get(f'/api/v1/parts/{test_part.id}', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == test_part.id
    assert data['name'] == test_part.name


def test_update_part(client, auth_headers, test_part):
    """Test updating a part."""
    response = client.put(f'/api/v1/parts/{test_part.id}', headers=auth_headers, json={
        'name': 'Updated CPU',
        'price': 399.99
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated CPU'
    assert data['price'] == 399.99


def test_delete_part(client, auth_headers, test_part):
    """Test deleting a part."""
    response = client.delete(f'/api/v1/parts/{test_part.id}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/api/v1/parts/{test_part.id}', headers=auth_headers)
    assert get_response.status_code == 404


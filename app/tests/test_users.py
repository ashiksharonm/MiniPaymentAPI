"""
Tests for User API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestCreateUser:
    """Tests for user creation endpoint."""
    
    def test_create_user_success(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict
    ):
        """Test successful user creation."""
        response = client.post("/users", json=sample_user_data, headers=api_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert data["country"] == sample_user_data["country"].upper()
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_duplicate_email(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict
    ):
        """Test that duplicate emails are rejected with 409."""
        # Create first user
        response1 = client.post("/users", json=sample_user_data, headers=api_headers)
        assert response1.status_code == 201
        
        # Attempt to create second user with same email
        response2 = client.post("/users", json=sample_user_data, headers=api_headers)
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
    
    def test_create_user_invalid_email(
        self, 
        client: TestClient, 
        api_headers: dict
    ):
        """Test that invalid emails are rejected with 422."""
        invalid_data = {
            "name": "Test User",
            "email": "invalid-email",
            "country": "US"
        }
        
        response = client.post("/users", json=invalid_data, headers=api_headers)
        
        assert response.status_code == 422
    
    def test_create_user_invalid_country_code(
        self, 
        client: TestClient, 
        api_headers: dict
    ):
        """Test that invalid country codes are rejected."""
        invalid_data = {
            "name": "Test User",
            "email": "test@example.com",
            "country": "USA"  # Should be 2 characters
        }
        
        response = client.post("/users", json=invalid_data, headers=api_headers)
        
        assert response.status_code == 422
    
    def test_create_user_missing_fields(
        self, 
        client: TestClient, 
        api_headers: dict
    ):
        """Test that missing required fields are rejected."""
        incomplete_data = {"name": "Test User"}
        
        response = client.post("/users", json=incomplete_data, headers=api_headers)
        
        assert response.status_code == 422
    
    def test_create_user_without_api_key(
        self, 
        client: TestClient, 
        sample_user_data: dict
    ):
        """Test that requests without API key are rejected."""
        response = client.post("/users", json=sample_user_data)
        
        assert response.status_code == 401


class TestGetUser:
    """Tests for user retrieval endpoint."""
    
    def test_get_user_success(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict
    ):
        """Test successful user retrieval."""
        # Create user first
        create_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = create_response.json()["id"]
        
        # Get the user
        response = client.get(f"/users/{user_id}", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]
    
    def test_get_user_not_found(
        self, 
        client: TestClient, 
        api_headers: dict
    ):
        """Test that non-existent user returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/users/{fake_id}", headers=api_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_user_without_api_key(
        self, 
        client: TestClient
    ):
        """Test that requests without API key are rejected."""
        response = client.get("/users/some-id")
        
        assert response.status_code == 401

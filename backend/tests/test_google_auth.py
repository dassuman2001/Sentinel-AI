from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from app.config.settings import settings

def test_google_login_register_and_login_flow(client):
    # 1. Prepare mock tokeninfo response from Google
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": settings.GOOGLE_CLIENT_ID,
        "email": "google-test@sentinel.ai",
        "given_name": "GoogleDev",
        "family_name": "User",
        "email_verified": True
    }
    
    # 2. Mock httpx.AsyncClient.get as an AsyncMock
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        # Call google-login endpoint with is_signup=True (should register user and log in)
        response = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "valid_google_credential_token", "is_signup": True}
        )
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Verify the mock endpoint was hit with the proper URL
        mock_get.assert_called_once_with(
            f"https://oauth2.googleapis.com/tokeninfo?id_token=valid_google_credential_token"
        )

    # 3. Call the google-login endpoint again with is_signup=False (should log in existing user without duplicating)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get2:
        mock_get2.return_value = mock_response
        
        response2 = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "another_valid_credential", "is_signup": False}
        )
        assert response2.status_code == 200
        token_data2 = response2.json()
        assert "access_token" in token_data2
        
        # Use access token to fetch user profile and verify fields
        headers = {"Authorization": f"Bearer {token_data2['access_token']}"}
        profile_res = client.get("/api/v1/users/me", headers=headers)
        assert profile_res.status_code == 200
        profile_data = profile_res.json()
        assert profile_data["email"] == "google-test@sentinel.ai"
        assert profile_data["first_name"] == "GoogleDev"
        assert profile_data["last_name"] == "User"

def test_google_login_invalid_token(client):
    # Mock a failed token verification response from Google (e.g. 400 Bad Request)
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error_description": "Invalid Value"}
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "invalid_or_expired_token", "is_signup": False}
        )
        assert response.status_code == 401
        assert "Invalid Google OAuth token" in response.json()["detail"]

def test_google_login_audience_mismatch(client):
    # Mock tokeninfo response with mismatched audience
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": "mismatched_client_id_hacker",
        "email": "hacker@sentinel.ai",
        "given_name": "Hacker",
        "family_name": "User",
        "email_verified": True
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "hacked_token", "is_signup": False}
        )
        assert response.status_code == 401
        assert "Token audience (aud) mismatch" in response.json()["detail"]

def test_google_login_signup_already_exists(client):
    # Prepare mock tokeninfo response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": settings.GOOGLE_CLIENT_ID,
        "email": "google-test-dup@sentinel.ai",
        "given_name": "GoogleDev",
        "family_name": "User",
        "email_verified": True
    }
    
    # Mock httpx.AsyncClient.get
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        # 1. First signup call (should succeed)
        response1 = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "valid_google_credential_token", "is_signup": True}
        )
        assert response1.status_code == 200
        
        # 2. Second signup call (should fail since it already exists)
        response2 = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "valid_google_credential_token", "is_signup": True}
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

def test_google_login_signin_not_found(client):
    # Prepare mock tokeninfo response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": settings.GOOGLE_CLIENT_ID,
        "email": "nonexistent-google-user@sentinel.ai",
        "given_name": "New",
        "family_name": "User",
        "email_verified": True
    }
    
    # Mock httpx.AsyncClient.get
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        # Call google-login with is_signup=False (should fail since user doesn't exist)
        response = client.post(
            "/api/v1/auth/google-login",
            json={"credential": "valid_google_credential_token", "is_signup": False}
        )
        
        assert response.status_code == 404
        assert "No account associated" in response.json()["detail"]

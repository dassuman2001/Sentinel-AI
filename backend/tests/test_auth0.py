from unittest.mock import patch, AsyncMock, MagicMock
import pytest

def test_auth0_login_register_and_login_flow(client):
    # 1. Prepare mock userinfo response from Auth0
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "google-oauth2|1234567890",
        "email": "auth0-test@sentinel.ai",
        "given_name": "Google",
        "family_name": "User",
        "email_verified": True
    }
    
    # 2. Mock httpx.AsyncClient.get as an AsyncMock
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        # Call auth0-login endpoint (should register the user and login)
        response = client.post(
            "/api/v1/auth/auth0-login",
            json={"token": "valid_google_token_xyz"}
        )
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Verify the mock endpoint was hit with appropriate headers
        mock_get.assert_called_once_with(
            "https://sentinel-ai.us.auth0.com/userinfo",
            headers={"Authorization": "Bearer valid_google_token_xyz"}
        )

    # 3. Call the auth0-login endpoint again (should log in existing user without duplicating)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get2:
        mock_get2.return_value = mock_response
        
        response2 = client.post(
            "/api/v1/auth/auth0-login",
            json={"token": "another_valid_token"}
        )
        assert response2.status_code == 200
        token_data2 = response2.json()
        assert "access_token" in token_data2
        
        # Use access token to fetch user profile and verify fields
        headers = {"Authorization": f"Bearer {token_data2['access_token']}"}
        profile_res = client.get("/api/v1/users/me", headers=headers)
        assert profile_res.status_code == 200
        profile_data = profile_res.json()
        assert profile_data["email"] == "auth0-test@sentinel.ai"
        assert profile_data["first_name"] == "Google"
        assert profile_data["last_name"] == "User"

def test_auth0_login_invalid_token(client):
    # Mock a failed token verification response from Auth0 (e.g. 401 Unauthorized)
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/auth0-login",
            json={"token": "invalid_or_expired_token"}
        )
        assert response.status_code == 401
        assert "Invalid Auth0 token" in response.json()["detail"]

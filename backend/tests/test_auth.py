from app.security.auth import hash_password, verify_password

def test_password_hashing():
    password = "secretpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_user_registration_and_login(client):
    # 1. Register a new user
    register_payload = {
        "email": "dev@sentinel.ai",
        "password": "strongPassword123",
        "first_name": "Sentinel",
        "last_name": "Developer"
    }
    
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "dev@sentinel.ai"
    assert user_data["first_name"] == "Sentinel"
    # Verify first user registered becomes admin
    assert user_data["role"] == "admin"
    assert "id" in user_data
    
    # 2. Prevent duplicate registrations
    dup_response = client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400
    
    # 3. Log in with the registered user
    login_payload = {
        "username": "dev@sentinel.ai",
        "password": "strongPassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # 4. Fetch user profile utilizing access token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = client.get("/api/v1/users/me", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == "dev@sentinel.ai"
    assert profile_data["role"] == "admin"
    
    # 5. Verify failed authentication with invalid token
    bad_headers = {"Authorization": "Bearer invalidtokenvalue"}
    bad_response = client.get("/api/v1/users/me", headers=bad_headers)
    assert bad_response.status_code == 401

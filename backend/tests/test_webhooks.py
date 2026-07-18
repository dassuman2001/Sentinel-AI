import pytest
from unittest.mock import patch
from app import models

@pytest.fixture
def sample_user(db):
    user = models.User(
        email="test@example.com",
        hashed_password="fakehashpassword",
        first_name="Test",
        last_name="User",
        is_active=True,
        role="developer"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def sample_repo(db, sample_user):
    repo = models.Repository(
        user_id=sample_user.id,
        name="test-repo",
        clone_url="https://github.com/test/repo.git",
        provider="github",
        is_active=True
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

@patch("app.api.v1.endpoints.webhooks.run_repository_scan.delay")
def test_github_webhook_success(mock_delay, client, db, sample_repo):
    payload = {
        "ref": "refs/heads/feature/oauth",
        "after": "abcdef1234567890",
        "repository": {
            "name": "test-repo",
            "clone_url": "https://github.com/test/repo.git"
        }
    }
    
    response = client.post(
        f"/api/v1/webhooks/github/{sample_repo.id}",
        json=payload
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["branch"] == "feature/oauth"
    assert data["commit"] == "abcdef1234567890"
    
    # Assert Celery task triggered
    mock_delay.assert_called_once()
    
    # Assert Scan record created
    scan_id = data["scan_id"]
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    assert scan is not None
    assert scan.repository_id == sample_repo.id
    assert scan.status == "pending"
    assert scan.commit_hash == "abcdef1234567890"

@patch("app.api.v1.endpoints.webhooks.run_repository_scan.delay")
def test_gitlab_webhook_success(mock_delay, client, db, sample_repo):
    payload = {
        "ref": "refs/heads/main",
        "checkout_sha": "9876543210fedcba"
    }
    
    response = client.post(
        f"/api/v1/webhooks/gitlab/{sample_repo.id}",
        json=payload
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["branch"] == "main"
    assert data["commit"] == "9876543210fedcba"
    
    # Assert Celery task triggered
    mock_delay.assert_called_once()

def test_webhook_repo_not_found(client):
    response = client.post(
        "/api/v1/webhooks/github/99999",
        json={"ref": "refs/heads/main"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found."

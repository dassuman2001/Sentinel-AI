import pytest
from app.models.organization import Organization
from app.models.project import Project
from app.models.repository import Repository, Branch
from app.models.scan import Scan
from app.models.secret import Secret
from app.models.ai_analysis import AIAnalysis

def test_ai_endpoints_workflow(client, db):
    # 1. Register and get token
    register_payload = {
        "email": "dev@sentinel.ai",
        "password": "strongPassword123",
        "first_name": "Sentinel",
        "last_name": "Developer"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_payload = {
        "username": "dev@sentinel.ai",
        "password": "strongPassword123"
    }
    login_res = client.post("/api/v1/auth/login", data=login_payload)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed a repository, branch, scan, and secret in DB
    from app.models.user import User
    user = db.query(User).filter(User.email == "dev@sentinel.ai").first()

    repo = Repository(
        name="test-repo",
        clone_url="https://github.com/test/repo",
        user_id=user.id
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    branch = Branch(repository_id=repo.id, name="main")
    db.add(branch)
    db.commit()
    db.refresh(branch)

    scan = Scan(repository_id=repo.id, branch_id=branch.id, status="completed")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    secret = Secret(
        scan_id=scan.id,
        repository_id=repo.id,
        file_path="main.py",
        line_number=10,
        secret_type="AWS Access Key",
        detected_value_hashed="hashedvalue123",
        masked_value="AKIAIOSFODNN7XXXXXXX",
        entropy=4.5,
        raw_context="aws_key = 'AKIAIOSFODNN7XXXXXXX'",
        status="active",
        severity="high"
    )
    db.add(secret)
    db.commit()
    db.refresh(secret)

    # 3. Call GET /api/v1/ai/explain/{secret_id}
    explain_res = client.get(f"/api/v1/ai/explain/{secret.id}", headers=headers)
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    
    assert explain_data["secret_id"] == secret.id
    assert "explanation" in explain_data
    assert "remediation" in explain_data
    
    # Check explanation structure
    exp = explain_data["explanation"]
    assert "danger_description" in exp
    assert "risk_level" in exp
    assert "exploitation_scenario" in exp
    assert "business_impact" in exp

    # Check remediation structure
    rem = explain_data["remediation"]
    assert "safe_code" in rem
    assert "env_template" in rem
    assert "rotation_steps" in rem

    # 4. Check that AIAnalysis cached entry is present in DB
    cached = db.query(AIAnalysis).filter(AIAnalysis.secret_id == secret.id).first()
    assert cached is not None
    assert cached.secret_id == secret.id

    # 5. Call POST /api/v1/ai/chat/{secret_id}
    chat_payload = {"question": "How do I rotate my AWS keys?"}
    chat_res = client.post(f"/api/v1/ai/chat/{secret.id}", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert len(chat_data["answer"]) > 0

from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app import models
from app.database.session import get_db
from app.tasks.scan_tasks import run_repository_scan

logger = logging.getLogger("sentinel.webhooks")
router = APIRouter()

@router.post("/github/{repo_id}", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    repo_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Receives a push webhook from GitHub and automatically triggers a scan.
    """
    logger.info(f"Received GitHub webhook for repo_id: {repo_id}")
    
    # 1. Fetch Repository
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
        
    # 2. Parse payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )
        
    ref = payload.get("ref", "refs/heads/main")
    branch_name = "main"
    if ref and ref.startswith("refs/heads/"):
        branch_name = ref.replace("refs/heads/", "")
        
    commit_hash = payload.get("after")
    logger.info(f"Triggering auto-scan for {repo.name} branch={branch_name} commit={commit_hash}")
    
    # 3. Get or create Branch record
    branch = db.query(models.Branch).filter(
        models.Branch.repository_id == repo_id,
        models.Branch.name == branch_name
    ).first()
    
    if not branch:
        branch = models.Branch(
            repository_id=repo_id,
            name=branch_name,
            is_default=(branch_name == "main")
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
    # 4. Create Scan record
    scan = models.Scan(
        repository_id=repo_id,
        branch_id=branch.id,
        commit_hash=commit_hash,
        status="pending",
        total_files=0,
        secrets_found=0,
        risk_score=0.0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # 5. Enqueue scan task
    run_repository_scan.delay(
        scan.id,
        repo.id,
        repo.clone_url,
        branch.name,
        repo.access_token
    )
    
    return {
        "status": "queued",
        "scan_id": scan.id,
        "branch": branch_name,
        "commit": commit_hash
    }

@router.post("/gitlab/{repo_id}", status_code=status.HTTP_202_ACCEPTED)
async def gitlab_webhook(
    repo_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Receives a push webhook from GitLab and automatically triggers a scan.
    """
    logger.info(f"Received GitLab webhook for repo_id: {repo_id}")
    
    # 1. Fetch Repository
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
        
    # 2. Parse payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )
        
    ref = payload.get("ref", "refs/heads/main")
    branch_name = "main"
    if ref and ref.startswith("refs/heads/"):
        branch_name = ref.replace("refs/heads/", "")
        
    commit_hash = payload.get("checkout_sha")
    logger.info(f"Triggering auto-scan for GitLab {repo.name} branch={branch_name} commit={commit_hash}")
    
    # 3. Get or create Branch record
    branch = db.query(models.Branch).filter(
        models.Branch.repository_id == repo_id,
        models.Branch.name == branch_name
    ).first()
    
    if not branch:
        branch = models.Branch(
            repository_id=repo_id,
            name=branch_name,
            is_default=(branch_name == "main")
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
    # 4. Create Scan record
    scan = models.Scan(
        repository_id=repo_id,
        branch_id=branch.id,
        commit_hash=commit_hash,
        status="pending",
        total_files=0,
        secrets_found=0,
        risk_score=0.0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # 5. Enqueue scan task
    run_repository_scan.delay(
        scan.id,
        repo.id,
        repo.clone_url,
        branch.name,
        repo.access_token
    )
    
    return {
        "status": "queued",
        "scan_id": scan.id,
        "branch": branch_name,
        "commit": commit_hash
    }

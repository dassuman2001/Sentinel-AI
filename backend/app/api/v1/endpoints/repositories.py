import os
import logging
import git
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth
from app.tasks.scan_tasks import run_repository_scan

logger = logging.getLogger("sentinel.repositories")

router = APIRouter()

@router.post("/", response_model=schemas.RepositoryOut, status_code=status.HTTP_201_CREATED)
def register_repository(
    repo_in: schemas.RepositoryCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Register a new repository directly under the logged-in user."""
    db_repo = models.Repository(
        user_id=current_user.id,
        name=repo_in.name,
        clone_url=repo_in.clone_url,
        provider=repo_in.provider,
        access_token=repo_in.access_token,
        scan_schedule=repo_in.scan_schedule,
        is_active=True
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    
    # Create default main branch
    db_branch = models.Branch(
        repository_id=db_repo.id,
        name="main",
        is_default=True
    )
    db.add(db_branch)
    db.commit()
    
    return db_repo


@router.get("/", response_model=List[schemas.RepositoryOut])
def list_repositories(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List registered repositories for the current user."""
    if current_user.role == "admin":
        repos = db.query(models.Repository).all()
    else:
        repos = db.query(models.Repository).filter(models.Repository.user_id == current_user.id).all()
    return repos


@router.post("/{repo_id}/scan", response_model=schemas.ScanOut)
def trigger_scan(
    repo_id: int,
    branch_name: str = "main",
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Trigger a scanning job on the specified branch of the repository."""
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
        
    # Verify access
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    # Get or create branch record
    branch = db.query(models.Branch).filter(
        models.Branch.repository_id == repo_id,
        models.Branch.name == branch_name
    ).first()
    
    if not branch:
        branch = models.Branch(
            repository_id=repo_id,
            name=branch_name,
            is_default=False
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
    # Create Scan record in DB
    scan = models.Scan(
        repository_id=repo_id,
        branch_id=branch.id,
        status="pending",
        total_files=0,
        secrets_found=0,
        risk_score=0.0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Enqueue background Celery task
    run_repository_scan.delay(
        scan.id,
        repo.id,
        repo.clone_url,
        branch.name,
        repo.access_token
    )
    
    return scan


@router.get("/{repo_id}/branches/remote")
def get_remote_branches(
    repo_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Fetch the list of branches directly from the remote Git repository."""
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
        
    # Verify access
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    url = repo.clone_url
    # Support mock local path scanning for testing
    if url.startswith("local://"):
        local_path = url.replace("local://", "")
        if not os.path.exists(local_path):
            return {"branches": ["main"]}
        try:
            r = git.Repo(local_path)
            branches = [h.name for h in r.heads]
            return {"branches": branches if branches else ["main"]}
        except Exception:
            return {"branches": ["main"]}
            
    # Inject oauth token if present for HTTPS URLs
    if repo.access_token and url.startswith("https://"):
        url = url.replace("https://", f"https://oauth2:{repo.access_token}@")
        
    try:
        g = git.cmd.Git()
        output = g.ls_remote("--heads", url)
        branches = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                ref = parts[1]
                # refs/heads/some-branch -> some-branch
                branch_name = ref.replace("refs/heads/", "")
                branches.append(branch_name)
        if not branches:
            branches = ["main"]
        return {"branches": branches}
    except Exception as e:
        logger.error(f"Failed to fetch remote branches for repo {repo_id}: {str(e)}")
        # Return fallback default branches on any error
        return {"branches": ["main", "master"]}

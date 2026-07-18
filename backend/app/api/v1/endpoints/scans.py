from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.get("/", response_model=List[schemas.ScanOut])
def get_scans_history(
    repository_id: Optional[int] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get scan history list for a repository or user."""
    query = db.query(models.Scan)
    if current_user.role != "admin":
        query = query.join(models.Repository).filter(models.Repository.user_id == current_user.id)
        
    if repository_id is not None:
        repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found.")
        if repo.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied.")
        query = query.filter(models.Scan.repository_id == repository_id)
        
    scans = query.order_by(models.Scan.created_at.desc()).all()
    return scans


@router.get("/{scan_id}", response_model=schemas.ScanOut)
def get_scan_details(
    scan_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve detailed scan status and results."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
        
    # Check access
    repo = db.query(models.Repository).filter(models.Repository.id == scan.repository_id).first()
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    return scan

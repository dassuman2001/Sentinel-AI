from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.get("/", response_model=List[schemas.SecretOut])
def list_secrets(
    repository_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List detected secrets with optional filtering by repository, scan, severity, and status."""
    query = db.query(models.Secret)
    
    if current_user.role != "admin":
        query = query.join(models.Repository).filter(models.Repository.user_id == current_user.id)

    if repository_id is not None:
        # Check access to repository
        repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found.")
        if repo.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied.")
        query = query.filter(models.Secret.repository_id == repository_id)
        
    if scan_id is not None:
        query = query.filter(models.Secret.scan_id == scan_id)
        
    if severity is not None:
        query = query.filter(models.Secret.severity == severity.lower())
        
    if status is not None:
        query = query.filter(models.Secret.status == status.lower())
        
    secrets = query.order_by(models.Secret.created_at.desc()).all()
    return secrets


@router.put("/{secret_id}/status", response_model=schemas.SecretOut)
def update_secret_status(
    secret_id: int,
    status_in: schemas.SecretStatusUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update status of a secret (active, resolved, false_positive)."""
    valid_statuses = {"active", "resolved", "false_positive"}
    if status_in.status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
        
    secret = db.query(models.Secret).filter(models.Secret.id == secret_id).first()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found.")
        
    # Check authorization
    repo = db.query(models.Repository).filter(models.Repository.id == secret.repository_id).first()
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    secret.status = status_in.status.lower()
    
    # Audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="SECRET_STATUS_CHANGED",
        details=f"Changed secret {secret_id} status to {status_in.status.lower()}"
    )
    db.add(audit_log)
    db.commit()
    db.refresh(secret)
    return secret

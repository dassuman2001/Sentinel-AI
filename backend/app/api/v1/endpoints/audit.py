from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.get("/", response_model=List[schemas.AuditLogOut])
def list_audit_logs(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List audit logs scoped to the current user."""
    if current_user.role == "admin":
        logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).all()
    else:
        logs = db.query(models.AuditLog).filter(models.AuditLog.user_id == current_user.id).order_by(models.AuditLog.created_at.desc()).all()
    return logs

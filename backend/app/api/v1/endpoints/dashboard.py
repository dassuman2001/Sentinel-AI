from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.get("/stats")
def get_dashboard_statistics(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get aggregated metrics and counts for the dashboard overview."""
    # Standard users see statistics restricted to their organizations
    # Admin users see global statistics
    if current_user.role == "admin":
        total_repos = db.query(models.Repository).count()
        total_scans = db.query(models.Scan).count()
        total_secrets = db.query(models.Secret).filter(models.Secret.status == "active").count()
        avg_risk = db.query(func.avg(models.Scan.risk_score)).filter(models.Scan.status == "completed").scalar() or 100.0
    else:
        repo_query = db.query(models.Repository.id).filter(
            models.Repository.user_id == current_user.id
        ).subquery()
        
        total_repos = db.query(models.Repository).filter(models.Repository.id.in_(repo_query)).count()
        total_scans = db.query(models.Scan).filter(models.Scan.repository_id.in_(repo_query)).count()
        total_secrets = db.query(models.Secret).filter(
            models.Secret.repository_id.in_(repo_query),
            models.Secret.status == "active"
        ).count()
        
        avg_risk = db.query(func.avg(models.Scan.risk_score)).filter(
            models.Scan.repository_id.in_(repo_query),
            models.Scan.status == "completed"
        ).scalar() or 100.0
        
    return {
        "total_repositories": total_repos,
        "total_scans": total_scans,
        "secrets_found": total_secrets,
        "average_risk_score": round(float(avg_risk), 1)
    }


@router.get("/charts/secrets-by-severity")
def get_secrets_by_severity(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get count of active secrets grouped by severity."""
    if current_user.role == "admin":
        results = db.query(
            models.Secret.severity,
            func.count(models.Secret.id)
        ).filter(models.Secret.status == "active").group_by(models.Secret.severity).all()
    else:
        repo_query = db.query(models.Repository.id).filter(
            models.Repository.user_id == current_user.id
        ).subquery()
        
        results = db.query(
            models.Secret.severity,
            func.count(models.Secret.id)
        ).filter(
            models.Secret.repository_id.in_(repo_query),
            models.Secret.status == "active"
        ).group_by(models.Secret.severity).all()
        
    # Format to dict
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for severity, count in results:
        severity_counts[severity.lower()] = count
        
    return severity_counts


@router.get("/charts/secrets-by-type")
def get_secrets_by_type(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get active secrets breakdown by secret type."""
    if current_user.role == "admin":
        results = db.query(
            models.Secret.secret_type,
            func.count(models.Secret.id)
        ).filter(models.Secret.status == "active").group_by(models.Secret.secret_type).all()
    else:
        repo_query = db.query(models.Repository.id).filter(
            models.Repository.user_id == current_user.id
        ).subquery()
        
        results = db.query(
            models.Secret.secret_type,
            func.count(models.Secret.id)
        ).filter(
            models.Secret.repository_id.in_(repo_query),
            models.Secret.status == "active"
        ).group_by(models.Secret.secret_type).all()
        
    return {secret_type: count for secret_type, count in results}

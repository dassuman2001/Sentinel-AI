from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.post("/", response_model=schemas.OrgOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: schemas.OrgCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new organization and make the creator the owner."""
    # Check if slug unique
    existing_org = db.query(models.Organization).filter(models.Organization.slug == org_in.slug).first()
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization slug is already in use. Please select another slug."
        )
        
    db_org = models.Organization(
        name=org_in.name,
        slug=org_in.slug,
        billing_status="free"
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    # Associate user as Organization Owner
    user_org = models.UserOrganization(
        user_id=current_user.id,
        organization_id=db_org.id,
        role="owner"
    )
    db.add(user_org)
    db.commit()
    
    return db_org


@router.get("/", response_model=List[schemas.OrgOut])
def list_my_organizations(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List organizations the current user belongs to."""
    orgs = db.query(models.Organization).join(models.UserOrganization).filter(
        models.UserOrganization.user_id == current_user.id
    ).all()
    return orgs


@router.get("/{org_id}/members", response_model=List[schemas.OrgMemberOut])
def get_organization_members(
    org_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get members of an organization."""
    # Check if current user is member of the organization
    user_org_check = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id
    ).first()
    
    if not user_org_check and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this organization's members."
        )
        
    members = db.query(
        models.User.id.label("user_id"),
        models.User.email,
        models.UserOrganization.role,
        models.User.first_name,
        models.User.last_name
    ).join(models.UserOrganization, models.User.id == models.UserOrganization.user_id).filter(
        models.UserOrganization.organization_id == org_id
    ).all()
    
    return members


@router.post("/{org_id}/teams", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    org_id: int,
    team_in: schemas.TeamCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a team in an organization (requires org owner or admin)."""
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id
    ).first()
    
    if (not user_org or user_org.role != "owner") and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only organization owners can create teams."
        )
        
    db_team = models.Team(
        organization_id=org_id,
        name=team_in.name
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.post("/{org_id}/projects", response_model=schemas.organization.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    org_id: int,
    project_in: schemas.organization.ProjectCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new project under an organization."""
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id
    ).first()
    
    if not user_org and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to create projects in this organization."
        )
        
    db_project = models.Project(
        organization_id=org_id,
        name=project_in.name,
        description=project_in.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/{org_id}/projects", response_model=List[schemas.organization.ProjectOut])
def list_projects(
    org_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List projects in an organization."""
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id
    ).first()
    
    if not user_org and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )
        
    projects = db.query(models.Project).filter(models.Project.organization_id == org_id).all()
    return projects


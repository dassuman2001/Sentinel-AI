from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut)
def read_user_me(
    current_user: models.User = Depends(auth.get_current_user)
) -> Any:
    """Retrieve current logged in user details."""
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_user_me(
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile info."""
    if user_in.first_name is not None:
        current_user.first_name = user_in.first_name
    if user_in.last_name is not None:
        current_user.last_name = user_in.last_name
    if user_in.email is not None:
        current_user.email = user_in.email
    if user_in.password is not None:
        current_user.hashed_password = auth.hash_password(user_in.password)
        
    db.commit()
    db.refresh(current_user)
    return current_user

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RepositoryBase(BaseModel):
    name: str
    clone_url: str
    provider: Optional[str] = "github"
    scan_schedule: Optional[str] = "manual"


class RepositoryCreate(RepositoryBase):
    access_token: Optional[str] = None


class RepositoryOut(RepositoryBase):
    id: int
    user_id: int
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BranchOut(BaseModel):
    id: int
    repository_id: int
    name: str
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# Teams
class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    pass


class TeamOut(TeamBase):
    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Organizations
class OrgBase(BaseModel):
    name: str
    slug: str


class OrgCreate(OrgBase):
    pass


class OrgOut(OrgBase):
    id: int
    billing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrgMemberOut(BaseModel):
    user_id: int
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrgInvite(BaseModel):
    email: str
    role: str = "member"


# Projects
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    organization_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

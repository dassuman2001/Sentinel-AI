from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ScanBase(BaseModel):
    repository_id: int
    branch_id: int
    commit_hash: Optional[str] = None


class ScanCreate(ScanBase):
    pass


class ScanOut(ScanBase):
    id: int
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_files: int
    secrets_found: int
    risk_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

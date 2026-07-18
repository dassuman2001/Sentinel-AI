from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SecretBase(BaseModel):
    scan_id: int
    repository_id: int
    file_path: str
    line_number: int
    column_number: int
    secret_type: str
    masked_value: str
    entropy: float
    status: str
    severity: str
    raw_context: Optional[str] = None


class SecretOut(SecretBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecretStatusUpdate(BaseModel):
    # E.g. "active", "resolved", "false_positive"
    status: str

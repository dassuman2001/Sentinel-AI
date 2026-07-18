from pydantic import BaseModel
from typing import Optional

class AIExplanationResponse(BaseModel):
    danger_description: str
    risk_level: str
    exploitation_scenario: str
    business_impact: str

class AIRemediationResponse(BaseModel):
    safe_code: str
    env_template: str
    rotation_steps: str

class AIChatRequest(BaseModel):
    question: str

class AIChatResponse(BaseModel):
    answer: str

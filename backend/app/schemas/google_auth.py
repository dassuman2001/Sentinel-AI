from pydantic import BaseModel

class GoogleLoginRequest(BaseModel):
    credential: str
    is_signup: bool = False

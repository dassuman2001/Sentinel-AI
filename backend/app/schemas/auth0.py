from pydantic import BaseModel

class Auth0Login(BaseModel):
    token: str

# app/schemas/weportal/auth.py
from pydantic import BaseModel, EmailStr


class WePortalLoginRequest(BaseModel):
    email: EmailStr
    password: str


class WePortalSession(BaseModel):
    id: str
    username: str
    email: str
    role: str
    empCode: str | None = None
    redirectTo: str
    accessToken: str
    tokenType: str = "bearer"


class WePortalLoginResponse(BaseModel):
    success: bool
    session: WePortalSession
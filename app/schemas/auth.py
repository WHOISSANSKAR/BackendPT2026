from pydantic import BaseModel, EmailStr, Field


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class CustomerLoginUser(BaseModel):
    id: int
    name: str
    email: EmailStr
    profile_complete: bool


class CustomerLoginResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    token_type: str
    redirect_to: str
    user: CustomerLoginUser
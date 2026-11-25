# from pydantic import BaseModel, EmailStr, Field


# class CustomerLoginRequest(BaseModel):
#     email: EmailStr
#     password: str = Field(min_length=1)


# class CustomerLoginUser(BaseModel):
#     id: int
#     name: str
#     email: EmailStr
#     profile_complete: bool


# class CustomerLoginResponse(BaseModel):
#     success: bool
#     message: str
#     access_token: str
#     token_type: str
#     redirect_to: str
#     user: CustomerLoginUser

# from typing import Any, Dict, Optional

# from pydantic import BaseModel, EmailStr, Field, field_validator


# # --- Sign Up & Verification ---

# class CustomerRegisterRequest(BaseModel):
#     name: str = Field(..., min_length=1, max_length=255)
#     email: EmailStr
#     contact: str = Field(..., min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
#     promo_code: Optional[str] = Field(default=None, max_length=255)

#     @field_validator("name", mode="before")
#     @classmethod
#     def strip_name(cls, v: str) -> str:
#         return v.strip() if isinstance(v, str) else v

#     @field_validator("email", mode="before")
#     @classmethod
#     def normalize_email(cls, v: str) -> str:
#         return v.strip().lower() if isinstance(v, str) else v


# class CustomerRegisterResponse(BaseModel):
#     success: bool
#     message: str
#     data: Optional[Dict[str, Any]] = None


# class CustomerSetPasswordRequest(BaseModel):
#     token: str = Field(..., min_length=10)
#     password: str = Field(..., min_length=8, max_length=128)
#     password_confirmation: str = Field(..., min_length=8, max_length=128)
#     user_id: Optional[int] = None
#     email: Optional[EmailStr] = None

#     @field_validator("password_confirmation")
#     @classmethod
#     def passwords_match(cls, v: str, info) -> str:
#         pw = info.data.get("password")
#         if pw is not None and v != pw:
#             raise ValueError("Password and confirmation do not match.")
#         return v


# class CustomerSetPasswordResponse(BaseModel):
#     success: bool
#     message: str
#     redirect_to: str = "/login"


# # --- Login ---

# class CustomerLoginRequest(BaseModel):
#     email: EmailStr
#     password: str = Field(min_length=1)

#     @field_validator("email", mode="before")
#     @classmethod
#     def normalize_email(cls, v: str) -> str:
#         return v.strip().lower() if isinstance(v, str) else v


# class CustomerLoginUser(BaseModel):
#     id: int
#     name: str
#     email: EmailStr
#     profile_complete: bool


# class CustomerLoginResponse(BaseModel):
#     success: bool
#     message: str
#     access_token: str
#     token_type: str
#     redirect_to: str
#     user: CustomerLoginUser

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Customer Sign Up & Set Password ---

class CustomerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    contact: str = Field(..., min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    promo_code: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


class CustomerRegisterResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class CustomerSetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        pw = info.data.get("password")
        if pw is not None and v != pw:
            raise ValueError("Password and confirmation do not match.")
        return v


class CustomerSetPasswordResponse(BaseModel):
    success: bool
    message: str
    redirect_to: str = "/login"


# --- Customer Login ---

class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


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
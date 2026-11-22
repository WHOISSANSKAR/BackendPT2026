
from pydantic import BaseModel, Field


class AccountProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    user_type: str | None = None
    organization: str | None = None


class AccountLocationUpdate(BaseModel):
    country: str | None = None
    state: str | None = None
    address: str | None = None
    pincode: str | None = None


class AccountIdentityUpdate(BaseModel):
    about: str | None = None
    organization_name: str | None = None
    cin: str | None = None
    gst_number: str | None = None
    aadhaar_number: str | None = None
    aadhaar_file_name: str | None = None


class AccountPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

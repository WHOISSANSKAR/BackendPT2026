from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
    CustomerSetPasswordRequest,
    CustomerSetPasswordResponse,
)
from app.services.auth_service import (
    customer_login,
    customer_register,
    customer_set_password,
    customer_verify_token,
)

router = APIRouter()


@router.post(
    "/customer/register",
    response_model=CustomerRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def customer_register_endpoint(
    request: CustomerRegisterRequest,
    db: Session = Depends(get_db),
):
    return customer_register(
        db=db,
        name=request.name,
        email=request.email,
        contact=request.contact,
        promo_code=request.promo_code,
    )


@router.get("/customer/verify")
def customer_verify_endpoint(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
):
    return customer_verify_token(db=db, token=token)


@router.post(
    "/customer/set-password",
    response_model=CustomerSetPasswordResponse,
)
def customer_set_password_endpoint(
    request: CustomerSetPasswordRequest,
    db: Session = Depends(get_db),
):
    return customer_set_password(
        db=db,
        token=request.token,
        password=request.password,
        user_id=request.user_id,
        email=request.email,
    )


@router.post(
    "/customer/login",
    response_model=CustomerLoginResponse,
)
def customer_login_endpoint(
    request: CustomerLoginRequest,
    db: Session = Depends(get_db),
):
    return customer_login(
        db=db,
        email=request.email,
        password=request.password,
    )
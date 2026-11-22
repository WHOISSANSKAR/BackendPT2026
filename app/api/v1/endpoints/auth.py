from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (
    CustomerLoginRequest,
    CustomerLoginResponse,
)
from app.services.auth_service import customer_login

router = APIRouter()


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
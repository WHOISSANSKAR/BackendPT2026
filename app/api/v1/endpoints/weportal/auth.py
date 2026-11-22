# app/api/v1/endpoints/weportal/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.weportal.auth import WePortalLoginRequest, WePortalLoginResponse
from app.services.weportal.auth_service import authenticate_weuser

router = APIRouter()


@router.post("/login", response_model=WePortalLoginResponse)
def weportal_login(
    payload: WePortalLoginRequest,
    db: Session = Depends(get_db),
):
    session_data = authenticate_weuser(db=db, credentials=payload)
    return WePortalLoginResponse(
        success=True,
        session=session_data,
    )
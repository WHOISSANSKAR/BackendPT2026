from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_weportal_access_token
from app.models.weuser import WeUser
from app.schemas.weportal.auth import WePortalLoginRequest, WePortalSession


def authenticate_weuser(
    db: Session,
    credentials: WePortalLoginRequest,
) -> WePortalSession:
    normalized_email = credentials.email.strip().lower()
    user = db.scalar(
        select(WeUser).where(func.lower(WeUser.email) == normalized_email)
    )

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password",
        )

    access_token = create_weportal_access_token(
        weuser_id=user.id,
        role=user.role,
        emp_code=user.emp_code,
    )

    redirect_to = (
        "/admin/project-restricted-view"
        if user.role == "viewer"
        else "/admin/index"
    )

    return WePortalSession(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        empCode=user.emp_code,
        redirectTo=redirect_to,
        accessToken=access_token,
    )
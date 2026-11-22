import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_customer_from_token(token: str, db: Session) -> ProjectOwner:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        # Prevent WePortal tokens from being accepted as customer tokens
        if payload.get("portal") == "weportal":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid portal token.",
            )

        customer_id = payload.get("sub")

        if customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    customer = db.scalar(
        select(ProjectOwner).where(
            ProjectOwner.pown_id == int(customer_id)
        )
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer account not found.",
        )

    return customer


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> ProjectOwner:
    return _decode_customer_from_token(credentials.credentials, db)


def get_current_customer_from_header_or_query(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ProjectOwner:
    raw_token = credentials.credentials if credentials else token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    return _decode_customer_from_token(raw_token, db)


def get_current_weuser(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> WeUser:
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        # Ensure token was issued specifically for WePortal
        if payload.get("portal") != "weportal":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted to WePortal users.",
            )

        weuser_id = payload.get("sub")

        if weuser_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    weuser = db.scalar(
        select(WeUser).where(
            WeUser.id == int(weuser_id)
        )
    )

    if not weuser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WePortal account not found.",
        )

    return weuser
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project_owner import ProjectOwner

from app.core.security import (
    verify_password,
    create_access_token,
)

from app.schemas.auth import (
    CustomerLoginResponse,
    CustomerLoginUser,
)


def customer_login(
    db: Session,
    email: str,
    password: str,
) -> CustomerLoginResponse:

    # STEP 1: Check email in users table with customer type
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.user_type == "customer",
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="These credentials do not match our records.",
        )

    # STEP 2: Find matching email in project_owners
    project_owner = db.scalar(
        select(ProjectOwner).where(
            ProjectOwner.pown_email == email
        )
    )

    if not project_owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with the provided email.",
        )

    # STEP 3: Verify password against project_owners table
    if not verify_password(
        password,
        project_owner.pown_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The provided credentials are incorrect.",
        )

    # STEP 4: Check profile completion
    profile_complete = bool(
        project_owner.pown_profile_completion_flag
    )

    # STEP 5: Generate JWT token
    access_token = create_access_token(
        customer_id=project_owner.pown_id
    )

    # STEP 6: Decide frontend destination
    redirect_to = (
        "/dashboard"
        if profile_complete
        else "/complete-profile"
    )

    # STEP 7: Return login response
    return CustomerLoginResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        token_type="bearer",
        redirect_to=redirect_to,
        user=CustomerLoginUser(
            id=project_owner.pown_id,
            name=project_owner.pown_name,
            email=project_owner.pown_email,
            profile_complete=profile_complete,
        ),
    )
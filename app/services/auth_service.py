import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.project_owner import ProjectOwner
from app.models.user import User
from app.schemas.auth import (
    CustomerLoginResponse,
    CustomerLoginUser,
    CustomerRegisterResponse,
    CustomerSetPasswordResponse,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)


def _get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")


def _get_verification_expire_hours() -> int:
    return int(os.getenv("VERIFICATION_EXPIRE_HOURS", "24"))


def _get_admin_notify_email() -> str:
    return os.getenv("ADMIN_NOTIFY_EMAIL", "").strip()


def _send_email(to_email: str, subject: str, body: str) -> None:
    smtp_host = (os.getenv("MAIL_HOST") or os.getenv("SMTP_HOST") or "").strip()
    smtp_port = int((os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT") or "587").strip())
    smtp_user = (os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
    mail_encryption = (os.getenv("MAIL_ENCRYPTION") or "tls").strip().lower()
    mail_from_addr = (
        os.getenv("MAIL_FROM_ADDRESS")
        or os.getenv("MAIL_FROM")
        or smtp_user
        or "info@pseudoteam.com"
    ).strip()
    mail_from_name = (os.getenv("MAIL_FROM_NAME") or "PseudoTeam Notification").strip().strip('"')

    if not smtp_host:
        logger.warning(
            "MAIL_HOST not configured; skipping email to %s. Subject: %s",
            to_email,
            subject,
        )
        logger.info("Verification/Email body for %s:\n%s", to_email, body)
        return

    msg = EmailMessage()
    msg["From"] = formataddr((mail_from_name, mail_from_addr)) if mail_from_name else mail_from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if mail_encryption == "ssl" or smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            if mail_encryption in ("tls", "starttls"):
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)


def _send_customer_verification_email(
    *,
    name: str,
    email: str,
    verification_link: str,
    created_at_str: str,
) -> None:
    expire_hours = _get_verification_expire_hours()
    admin_email = _get_admin_notify_email()

    customer_body = (
        f"Hello {name},\n\n"
        f"Thank you for signing up with PseudoTeam.\n"
        f"Please verify your email and set your password using the link below:\n\n"
        f"{verification_link}\n\n"
        f"This link will expire in {expire_hours} hours.\n\n"
        f"Best regards,\n"
        f"PseudoTeam"
    )
    _send_email(
        to_email=email,
        subject="Verify Your Email & Set Password - PseudoTeam",
        body=customer_body,
    )

    if admin_email:
        admin_body = (
            f"New Customer Signup:\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Registered At: {created_at_str}\n"
        )
        try:
            _send_email(
                to_email=admin_email,
                subject="New Customer Sign Up - PseudoTeam",
                body=admin_body,
            )
        except Exception as exc:
            logger.warning("Failed to send admin signup alert to %s: %s", admin_email, exc)


def _ensure_verification_token_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                email VARCHAR(255) NOT NULL,
                token VARCHAR(128) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                used_at DATETIME NULL,
                created_at DATETIME NOT NULL,
                INDEX idx_evt_token (token),
                INDEX idx_evt_user_id (user_id)
            )
            """
        )
    )


def customer_register(
    db: Session,
    *,
    name: str,
    email: str,
    contact: str,
    promo_code: Optional[str] = None,
) -> CustomerRegisterResponse:
    """
    Stores customer info in `users` AND `project_owners` on signup,
    creates a verification token, and sends the verification email.
    """
    _ensure_verification_token_table(db)

    normalized_email = email.strip().lower()
    clean_promo = promo_code.strip() if promo_code else None
    expire_hours = _get_verification_expire_hours()
    frontend_url = _get_frontend_url()

    if clean_promo:
        referral = db.execute(
            text("SELECT id FROM referral_table WHERE rfrls_promo_code = :code LIMIT 1"),
            {"code": clean_promo},
        ).fetchone()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"promo_code_error": ["Invalid promo code."]},
            )
        db.execute(
            text(
                "UPDATE referral_table SET rfrls_onboard_flag = 1 WHERE rfrls_promo_code = :code"
            ),
            {"code": clean_promo},
        )

    now_utc = datetime.now(timezone.utc)
    now_sql = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    now_short = now_utc.strftime("%Y-%m-%d")
    expires_at_sql = (now_utc + timedelta(hours=expire_hours)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # 1. Insert or update `users` table
    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user:
        user_id = existing_user.id
        db.execute(
            text(
                """
                UPDATE users
                SET name = :name,
                    contact = :contact,
                    user_type = 'customer',
                    updated_at = :now
                WHERE id = :user_id
                """
            ),
            {
                "name": name,
                "contact": contact,
                "now": now_sql,
                "user_id": user_id,
            },
        )
    else:
        db.execute(
            text(
                """
                INSERT INTO users (name, email, contact, user_type, created_at, updated_at)
                VALUES (:name, :email, :contact, 'customer', :now, :now)
                """
            ),
            {
                "name": name,
                "email": normalized_email,
                "contact": contact,
                "now": now_sql,
            },
        )
        user_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # 2. Insert or update `project_owners` table immediately on account creation
    clean_name = (name or "Customer").replace(" ", "")
    generated_promo = f"{clean_name}_{now_utc.strftime('%Y%m%d_%H%M%S')}"

    existing_owner = db.scalar(
        select(ProjectOwner).where(ProjectOwner.pown_email == normalized_email)
    )

    if existing_owner:
        pown_id = existing_owner.pown_id
        db.execute(
            text(
                """
                UPDATE project_owners
                SET pown_name = :name,
                    pown_contact = :contact,
                    pown_user_type = COALESCE(pown_user_type, 'customer'),
                    updated_at = :updated_at
                WHERE pown_id = :pown_id
                """
            ),
            {
                "name": name,
                "contact": contact,
                "updated_at": now_short,
                "pown_id": pown_id,
            },
        )
    else:
        db.execute(
            text(
                """
                INSERT INTO project_owners (
                    pown_name,
                    pown_email,
                    pown_contact,
                    pown_user_type,
                    pown_date_of_registration,
                    pown_login_flag,
                    pown_profile_completion_flag,
                    pown_promo_code,
                    pown_refered_by,
                    pown_verified,
                    created_at,
                    updated_at
                )
                VALUES (
                    :name,
                    :email,
                    :contact,
                    'customer',
                    :reg_date,
                    1,
                    0,
                    :promo_code,
                    :referred_by,
                    0,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "name": name,
                "email": normalized_email,
                "contact": contact,
                "reg_date": now_short,
                "promo_code": generated_promo,
                "referred_by": clean_promo,
                "created_at": now_short,
                "updated_at": now_short,
            },
        )
        pown_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # 3. Create verification token
    token = secrets.token_urlsafe(32)
    db.execute(
        text(
            """
            INSERT INTO email_verification_tokens (user_id, email, token, expires_at, created_at)
            VALUES (:user_id, :email, :token, :expires_at, :created_at)
            """
        ),
        {
            "user_id": user_id,
            "email": normalized_email,
            "token": token,
            "expires_at": expires_at_sql,
            "created_at": now_sql,
        },
    )
    db.commit()

    verification_link = (
        f"{frontend_url}/set-password"
        f"?token={token}&user_id={user_id}&email={normalized_email}"
    )

    try:
        _send_customer_verification_email(
            name=name,
            email=normalized_email,
            verification_link=verification_link,
            created_at_str=now_sql,
        )
    except Exception as exc:
        logger.exception("SMTP error sending verification email to %s: %s", normalized_email, exc)
        allow_dev_fallback = os.getenv("ALLOW_DEV_EMAIL_FALLBACK", "false").strip().lower() == "true"
        if allow_dev_fallback:
            logger.info("DEV FALLBACK verification link for %s: %s", normalized_email, verification_link)
            return CustomerRegisterResponse(
                success=True,
                message="Account created! (SMTP failed; check backend logs for verification link.)",
                data={
                    "user_id": user_id,
                    "project_owner_id": pown_id,
                    "email": normalized_email,
                    "redirect_to": "/login",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account created, but unable to send verification email: {exc}",
        )

    return CustomerRegisterResponse(
        success=True,
        message="Signup successful! Check your email for verification link.",
        data={
            "user_id": user_id,
            "project_owner_id": pown_id,
            "email": normalized_email,
            "redirect_to": "/login",
        },
    )


def customer_verify_token(db: Session, *, token: str) -> dict:
    _ensure_verification_token_table(db)
    now_sql = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    frontend_url = _get_frontend_url()

    row = db.execute(
        text(
            """
            SELECT id, user_id, email, expires_at, used_at
            FROM email_verification_tokens
            WHERE token = :token
            LIMIT 1
            """
        ),
        {"token": token},
    ).fetchone()

    if not row or row.used_at is not None or str(row.expires_at) < now_sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link.",
        )

    return {
        "success": True,
        "verified": True,
        "user_id": row.user_id,
        "email": row.email,
        "set_password_url": (
            f"{frontend_url}/set-password"
            f"?token={token}&user_id={row.user_id}&email={row.email}"
        ),
    }


def customer_set_password(
    db: Session,
    *,
    token: str,
    password: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> CustomerSetPasswordResponse:
    """
    Validates verification link token, reads `name`, `email`, `contact` from `users`,
    and sets password + verified status in `project_owners`.
    """
    _ensure_verification_token_table(db)
    now_utc = datetime.now(timezone.utc)
    now_sql = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    now_short = now_utc.strftime("%Y-%m-%d")

    token_row = db.execute(
        text(
            """
            SELECT id, user_id, email, expires_at, used_at
            FROM email_verification_tokens
            WHERE token = :token
            LIMIT 1
            """
        ),
        {"token": token},
    ).fetchone()

    if not token_row or token_row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used verification link.",
        )

    if str(token_row.expires_at) < now_sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please sign up again.",
        )

    if user_id is not None and user_id != token_row.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token does not match the specified user.",
        )

    if email is not None and email.strip().lower() != str(token_row.email).strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token does not match the specified email.",
        )

    user = db.scalar(select(User).where(User.id == token_row.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    hashed_pw = get_password_hash(password)
    clean_name = (user.name or "Customer").replace(" ", "")
    generated_promo = f"{clean_name}_{now_utc.strftime('%Y%m%d_%H%M%S')}"

    existing_owner = db.scalar(
        select(ProjectOwner).where(ProjectOwner.pown_email == user.email)
    )

    if existing_owner:
        db.execute(
            text(
                """
                UPDATE project_owners
                SET pown_name = :name,
                    pown_contact = :contact,
                    pown_password = :password,
                    pown_verified = 1,
                    updated_at = :updated_at
                WHERE pown_id = :pown_id
                """
            ),
            {
                "name": user.name,
                "contact": user.contact,
                "password": hashed_pw,
                "updated_at": now_short,
                "pown_id": existing_owner.pown_id,
            },
        )
    else:
        db.execute(
            text(
                """
                INSERT INTO project_owners (
                    pown_name,
                    pown_email,
                    pown_contact,
                    pown_user_type,
                    pown_date_of_registration,
                    pown_password,
                    pown_login_flag,
                    pown_profile_completion_flag,
                    pown_promo_code,
                    pown_verified,
                    created_at,
                    updated_at
                )
                VALUES (
                    :name,
                    :email,
                    :contact,
                    'customer',
                    :reg_date,
                    :password,
                    1,
                    0,
                    :promo_code,
                    1,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "name": user.name,
                "email": user.email,
                "contact": user.contact,
                "reg_date": now_short,
                "password": hashed_pw,
                "promo_code": generated_promo,
                "created_at": now_short,
                "updated_at": now_short,
            },
        )

    db.execute(
        text("UPDATE email_verification_tokens SET used_at = :now WHERE id = :id"),
        {"now": now_sql, "id": token_row.id},
    )
    db.commit()

    return CustomerSetPasswordResponse(
        success=True,
        message="Password set successfully! You can now log in.",
        redirect_to="/login",
    )


def customer_login(
    db: Session,
    email: str,
    password: str,
) -> CustomerLoginResponse:
    normalized_email = email.strip().lower()

    # STEP 1: Check email in users table with customer type
    user = db.scalar(
        select(User).where(
            User.email == normalized_email,
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
            ProjectOwner.pown_email == normalized_email
        )
    )

    if not project_owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with the provided email.",
        )

    # STEP 3: Verify password against project_owners table
    if not project_owner.pown_password or not verify_password(
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
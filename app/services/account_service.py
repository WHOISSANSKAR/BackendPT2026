
from fastapi import HTTPException
from sqlalchemy.orm import Session
import bcrypt

from app.models.project_owner import ProjectOwner


# --------------------------------------------------
# GET CUSTOMER
# --------------------------------------------------

def get_attached_customer(
    db: Session,
    current_customer,
) -> ProjectOwner:

    customer = (
        db.query(ProjectOwner)
        .filter(
            ProjectOwner.pown_id == current_customer.pown_id
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer account not found",
        )

    return customer


# --------------------------------------------------
# SERIALIZE ACCOUNT
# --------------------------------------------------

def serialize_account(customer: ProjectOwner):

    full_name = customer.pown_name or ""

    name_parts = full_name.strip().split(maxsplit=1)

    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "id": customer.pown_id,

        # Profile information
        "username": customer.pown_username,
        "firstName": first_name,
        "lastName": last_name,
        "fullName": full_name,
        "email": customer.pown_email,
        "phone": customer.pown_contact,
        "userType": customer.pown_user_type,
        "organization": customer.pown_organisation_name,

        # Location information
        "country": customer.pown_country,
        "state": customer.pown_state,
        "address": customer.pown_address,
        "pincode": customer.pown_pincode,

        # Identity information
        "about": customer.pown_about,
        "cin": customer.pown_cin,
        "gstNumber": customer.pown_gstpin,
        "aadhaarNumber": customer.pown_adhaar,
        "aadhaarFileName": customer.pown_adhaarfile,

        # Account information
        "body": customer.pown_body,
        "dateOfRegistration": customer.pown_date_of_registration,
        "referredBy": customer.pown_refered_by,
        "promoCode": customer.pown_promo_code,

        # Account status
        "verified": customer.pown_verified,
        "profileCompletion": customer.pown_profile_completion_flag,
        "loginEnabled": customer.pown_login_flag,

        # Avatar information
        "hasAvatar": bool(customer.pown_dp),

        # Account timestamps
        "createdAt": customer.created_at,
        "updatedAt": customer.updated_at,

        # Never return the password or password hash.
    }


# --------------------------------------------------
# GET ACCOUNT PROFILE
# --------------------------------------------------

def get_account_profile(
    db: Session,
    current_customer,
):

    customer = get_attached_customer(db, current_customer)

    return {
        "success": True,
        "message": "Account profile fetched successfully",
        "profile": serialize_account(customer),
    }


# --------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------

def update_account_profile(
    db: Session,
    current_customer,
    data: dict,
):

    customer = get_attached_customer(db, current_customer)

    first_name = data.get("first_name")
    last_name = data.get("last_name")

    # Update full name
    if first_name is not None or last_name is not None:

        existing_parts = (
            customer.pown_name or ""
        ).strip().split(maxsplit=1)

        current_first = (
            existing_parts[0] if existing_parts else ""
        )

        current_last = (
            existing_parts[1] if len(existing_parts) > 1 else ""
        )

        first_name = (
            first_name if first_name is not None else current_first
        )

        last_name = (
            last_name if last_name is not None else current_last
        )

        customer.pown_name = (
            f"{first_name.strip()} {last_name.strip()}"
        ).strip()

    field_mapping = {
        "email": "pown_email",
        "phone": "pown_contact",
        "user_type": "pown_user_type",
        "organization": "pown_organisation_name",
    }

    for input_field, db_field in field_mapping.items():

        if input_field in data:
            setattr(
                customer,
                db_field,
                data[input_field],
            )

    db.commit()
    db.refresh(customer)

    return {
        "success": True,
        "message": "Profile updated successfully",
        "profile": serialize_account(customer),
    }


# --------------------------------------------------
# UPDATE LOCATION
# --------------------------------------------------

def update_account_location(
    db: Session,
    current_customer,
    data: dict,
):

    customer = get_attached_customer(db, current_customer)

    field_mapping = {
        "country": "pown_country",
        "state": "pown_state",
        "address": "pown_address",
        "pincode": "pown_pincode",
    }

    for input_field, db_field in field_mapping.items():

        if input_field in data:
            setattr(
                customer,
                db_field,
                data[input_field],
            )

    db.commit()
    db.refresh(customer)

    return {
        "success": True,
        "message": "Location updated successfully",
        "profile": serialize_account(customer),
    }


# --------------------------------------------------
# UPDATE IDENTITY
# --------------------------------------------------

def update_account_identity(
    db: Session,
    current_customer,
    data: dict,
):

    customer = get_attached_customer(db, current_customer)

    field_mapping = {
        "about": "pown_about",
        "organization_name": "pown_organisation_name",
        "cin": "pown_cin",
        "gst_number": "pown_gstpin",
        "aadhaar_number": "pown_adhaar",
        "aadhaar_file_name": "pown_adhaarfile",
    }

    for input_field, db_field in field_mapping.items():

        if input_field in data:
            setattr(
                customer,
                db_field,
                data[input_field],
            )

    db.commit()
    db.refresh(customer)

    return {
        "success": True,
        "message": "Identity information updated successfully",
        "profile": serialize_account(customer),
    }


# --------------------------------------------------
# UPDATE PASSWORD
# --------------------------------------------------

def update_account_password(
    db: Session,
    current_customer,
    data,
):

    customer = get_attached_customer(db, current_customer)

    stored_password = customer.pown_password

    if not stored_password:
        raise HTTPException(
            status_code=400,
            detail="Current password is not available for verification",
        )

    try:
        stored_hash = stored_password.encode("utf-8")

        # Support Laravel bcrypt hashes that use the $2y$ prefix.
        if stored_hash.startswith(b"$2y$"):
            stored_hash = b"$2b$" + stored_hash[4:]

        password_matches = bcrypt.checkpw(
            data.current_password.encode("utf-8"),
            stored_hash,
        )

    except (ValueError, TypeError):
        password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password",
        )

    new_password_hash = bcrypt.hashpw(
        data.new_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    customer.pown_password = new_password_hash

    db.commit()

    return {
        "success": True,
        "message": "Password updated successfully",
    }
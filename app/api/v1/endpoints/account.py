
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.schemas.account import (
    AccountProfileUpdate,
    AccountLocationUpdate,
    AccountIdentityUpdate,
    AccountPasswordUpdate,
)

from app.services.account_service import (
    get_attached_customer,
    get_account_profile,
    update_account_profile,
    update_account_location,
    update_account_identity,
    update_account_password,
)


router = APIRouter()


# --------------------------------------------------
# GET ACCOUNT PROFILE
# --------------------------------------------------

@router.get("/")
def fetch_account_profile(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return get_account_profile(db, current_customer)


# --------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------

@router.patch("/profile")
def save_account_profile(
    data: AccountProfileUpdate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return update_account_profile(
        db,
        current_customer,
        data.model_dump(exclude_unset=True),
    )


# --------------------------------------------------
# UPDATE LOCATION
# --------------------------------------------------

@router.patch("/location")
def save_account_location(
    data: AccountLocationUpdate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return update_account_location(
        db,
        current_customer,
        data.model_dump(exclude_unset=True),
    )


# --------------------------------------------------
# UPDATE IDENTITY
# --------------------------------------------------

@router.patch("/identity")
def save_account_identity(
    data: AccountIdentityUpdate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return update_account_identity(
        db,
        current_customer,
        data.model_dump(exclude_unset=True),
    )


# --------------------------------------------------
# UPDATE PASSWORD
# --------------------------------------------------

@router.patch("/password")
def save_account_password(
    data: AccountPasswordUpdate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return update_account_password(
        db,
        current_customer,
        data,
    )


# --------------------------------------------------
# GET PROFILE PICTURE
# --------------------------------------------------

@router.get("/avatar")
def fetch_customer_avatar(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer = get_attached_customer(db, current_customer)

    if not customer.pown_dp:
        raise HTTPException(
            status_code=404,
            detail="Profile picture not found",
        )

    # Detect common image formats using their file signatures.
    image_data = customer.pown_dp

    if image_data.startswith(b"\xff\xd8\xff"):
        media_type = "image/jpeg"
    elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        media_type = "image/png"
    elif image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        media_type = "image/webp"
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported profile picture format",
        )

    return Response(
        content=image_data,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
        },
    )


# --------------------------------------------------
# UPLOAD / REPLACE PROFILE PICTURE
# --------------------------------------------------

@router.put("/avatar")
async def upload_customer_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer = get_attached_customer(db, current_customer)

    allowed_types = {
        "image/jpeg": (
            b"\xff\xd8\xff",
        ),
        "image/png": (
            b"\x89PNG\r\n\x1a\n",
        ),
        "image/webp": (
            b"RIFF",
        ),
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed.",
        )

    image_data = await file.read()

    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    max_size = 5 * 1024 * 1024

    if len(image_data) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Image size must not exceed 5 MB.",
        )

    # Validate the actual image signature.
    if not image_data.startswith(allowed_types[file.content_type][0]):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not match its image format.",
        )

    if file.content_type == "image/webp":
        if image_data[8:12] != b"WEBP":
            raise HTTPException(
                status_code=400,
                detail="Invalid WEBP image.",
            )

    customer.pown_dp = image_data

    try:
        db.commit()
        db.refresh(customer)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save profile picture.",
        )

    return {
        "success": True,
        "message": "Profile picture uploaded successfully.",
        "hasAvatar": True,
    }


# --------------------------------------------------
# DELETE PROFILE PICTURE
# --------------------------------------------------

@router.delete("/avatar")
def delete_customer_avatar(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer = get_attached_customer(db, current_customer)

    if not customer.pown_dp:
        raise HTTPException(
            status_code=404,
            detail="Profile picture not found.",
        )

    customer.pown_dp = None

    try:
        db.commit()
        db.refresh(customer)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to remove profile picture.",
        )

    return {
        "success": True,
        "message": "Profile picture removed successfully.",
        "hasAvatar": False,
    }

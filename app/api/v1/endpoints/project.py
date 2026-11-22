from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import Project
from app.services.project_service import create_project
from app.core.dependencies import (
    get_current_customer,
    get_current_customer_from_header_or_query,
)


router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".zip",
}


def validate_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must use YYYY-MM-DD format.",
        )


def normalize_currency(value: str) -> str:
    # For example: "INR (₹)" becomes "INR".
    return value.split("(")[0].strip().upper()


def detect_sow_metadata(file_bytes: bytes, base_name: str) -> tuple[str, str, str]:
    """
    Detect file extension, MIME type, and download filename from magic bytes.
    """
    if file_bytes.startswith(b"%PDF"):
        return "pdf", "application/pdf", f"{base_name}_SOW.pdf"
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png", f"{base_name}_SOW.png"
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg", f"{base_name}_SOW.jpg"
    if file_bytes.startswith(b"PK\x03\x04"):
        header_chunk = file_bytes[:2048]
        if b"word/" in header_chunk:
            return (
                "docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                f"{base_name}_SOW.docx",
            )
        if b"xl/" in header_chunk:
            return (
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                f"{base_name}_SOW.xlsx",
            )
        return "zip", "application/zip", f"{base_name}_SOW.zip"
    if file_bytes.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc", "application/msword", f"{base_name}_SOW.doc"

    return "bin", "application/octet-stream", f"{base_name}_SOW.bin"


def format_iso_date(date_str: str | None) -> str | None:
    """Convert stored timestamp string into ISO format for frontend date rendering."""
    if not date_str:
        return None
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).isoformat()
        except ValueError:
            continue
    return None


@router.post("/projects", status_code=201)
async def upload_project(
    title: str = Form(...),
    description: str = Form(...),
    project_is: str = Form(...),
    project_type: str = Form(...),
    category: str = Form(...),
    currency: str = Form(...),
    budget: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    auth_person_name: str = Form(...),
    auth_person_email: str = Form(...),
    contact_number: str = Form(...),
    receive_notifications: bool = Form(False),
    additional_email: str | None = Form(None),
    promo_code: str | None = Form(None),
    sow_file: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    customer=Depends(get_current_customer),
):
    # 1. Validate required text fields (project_id is generated on backend).
    required_fields = {
        "title": title,
        "description": description,
        "project_is": project_is,
        "project_type": project_type,
        "category": category,
        "currency": currency,
        "auth_person_name": auth_person_name,
        "auth_person_email": auth_person_email,
        "contact_number": contact_number,
    }

    for field_name, value in required_fields.items():
        if not value.strip():
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} is required.",
            )

    # 2. Validate email(s).
    if "@" not in auth_person_email or "." not in auth_person_email.split("@")[-1]:
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid authorised person email.",
        )

    cleaned_additional_email = (
        additional_email.strip() if additional_email and additional_email.strip() else None
    )
    if receive_notifications and cleaned_additional_email:
        if "@" not in cleaned_additional_email or "." not in cleaned_additional_email.split("@")[-1]:
            raise HTTPException(
                status_code=422,
                detail="Please provide a valid additional email address.",
            )

    # 3. Validate dates.
    start = validate_date(start_date, "Start date")
    end = validate_date(end_date, "End date")

    if end < start:
        raise HTTPException(
            status_code=422,
            detail="End date cannot be earlier than start date.",
        )

    # 4. Validate budget.
    try:
        budget_value = Decimal(budget.replace(",", "").strip())

        if not budget_value.is_finite() or budget_value <= 0:
            raise ValueError

        if budget_value.as_tuple().exponent < -2:
            raise ValueError

        if budget_value >= Decimal("10000000000000"):
            raise ValueError

    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Budget must be a positive number with at most 2 decimal places.",
        )

    # 5. Validate and read the optional SOW file.
    file_bytes = None

    if sow_file is not None and sow_file.filename:
        extension = (
            "." + sow_file.filename.rsplit(".", 1)[-1].lower()
            if "." in sow_file.filename
            else ""
        )

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail="Unsupported file type. Allowed: JPG, JPEG, PNG, PDF, DOC, DOCX, XLS, XLSX, CSV, ZIP.",
            )

        file_bytes = await sow_file.read(MAX_FILE_SIZE + 1)

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="SOW file cannot exceed 50 MB.",
            )

        if not file_bytes:
            raise HTTPException(
                status_code=422,
                detail="The uploaded SOW file is empty.",
            )

    # 6. Get the customer ID from the authenticated JWT user.
    customer_id = str(customer.pown_id)

    # 7. Normalize currency.
    currency_code = normalize_currency(currency)

    # 8. Save using the project service (generates `Pseudo-YYYY-MMDDHHMMSS`).
    try:
        project = create_project(
            db,
            customer_id=customer_id,
            title=title.strip(),
            description=description.strip(),
            project_is=project_is.strip(),
            project_type=project_type.strip(),
            category=category.strip(),
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            currency=currency_code,
            budget=budget_value,
            auth_person_name=auth_person_name.strip(),
            auth_person_email=auth_person_email.strip(),
            contact_number=contact_number.strip(),
            sow_file=file_bytes,
            receive_notifications=receive_notifications,
            additional_email=cleaned_additional_email,
            promo_code=promo_code.strip() if promo_code and promo_code.strip() else None,
        )

    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save project. Please try again.",
        )

    # 9. Return the saved project details.
    return {
        "success": True,
        "message": "Project uploaded successfully.",
        "project": {
            "id": project.plist_id,
            "projectId": project.plist_projectid,
            "title": project.plist_title,
            "status": project.plist_project_status,
            "customerId": project.plist_customer_id,
            "sowUploaded": project.plist_sow is not None,
        },
    }


@router.get("/projects/{project_id}/documents")
def list_project_documents(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    customer=Depends(get_current_customer),
):
    customer_id = str(customer.pown_id)

    project = (
        db.query(Project)
        .filter(
            Project.plist_id == project_id,
            Project.plist_customer_id == customer_id,
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not project.plist_sow:
        return {"success": True, "documents": []}

    base_name = project.plist_projectid or f"PRJ-{project.plist_id}"
    ext, _, filename = detect_sow_metadata(project.plist_sow, base_name)

    # Forward the bearer token in the download URL so <a target="_blank"> works directly
    auth_header = request.headers.get("authorization", "")
    raw_token = auth_header.split(" ", 1)[1].strip() if auth_header.lower().startswith("bearer ") else ""
    download_url = f"/api/v1/customer/projects/{project.plist_id}/documents/sow"
    if raw_token:
        download_url = f"{download_url}?token={raw_token}"

    return {
        "success": True,
        "documents": [
            {
                "id": f"sow-{project.plist_id}",
                "name": filename,
                "file_type": ext,
                "size_bytes": len(project.plist_sow),
                "uploaded_at": format_iso_date(project.updated_at or project.created_at),
                "url": download_url,
            }
        ],
    }


@router.get("/projects/{project_id}/documents/sow")
def view_project_sow(
    project_id: int,
    db: Session = Depends(get_db),
    customer=Depends(get_current_customer_from_header_or_query),
):
    customer_id = str(customer.pown_id)

    project = (
        db.query(Project)
        .filter(
            Project.plist_id == project_id,
            Project.plist_customer_id == customer_id,
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not project.plist_sow:
        raise HTTPException(status_code=404, detail="No SOW or document found.")

    base_name = project.plist_projectid or f"PRJ-{project.plist_id}"
    _, media_type, filename = detect_sow_metadata(project.plist_sow, base_name)

    disposition = (
        "inline"
        if media_type in {"application/pdf", "image/png", "image/jpeg"}
        else "attachment"
    )

    return Response(
        content=project.plist_sow,
        media_type=media_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
        },
    )
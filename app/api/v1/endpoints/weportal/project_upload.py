from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.project_service import create_project

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


def _parse_iso_date(value: str, field_name: str) -> date:
    raw = (value or "").strip()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} ('{raw}') must use YYYY-MM-DD format.",
        )


def _normalize_currency(value: str | None) -> str:
    if not value or not value.strip():
        return "INR"
    return value.split("(")[0].strip().upper()


@router.post("/upload", status_code=201)
async def upload_weportal_project(
    customer_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    project_is: str = Form("New"),
    project_type: str = Form("General"),
    category: str = Form("General"),
    currency: str = Form("INR"),
    budget: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    auth_person_name: str = Form(...),
    auth_person_email: str = Form(...),
    contact_number: str = Form(...),
    receive_notifications: str | bool = Form(False),
    additional_email: str | None = Form(None),
    promo_code: str | None = Form(None),
    sow_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    required_fields = {
        "customer_id": customer_id,
        "title": title,
        "description": description,
        "auth_person_name": auth_person_name,
        "auth_person_email": auth_person_email,
        "contact_number": contact_number,
    }

    for field_name, value in required_fields.items():
        if not value or not str(value).strip():
            raise HTTPException(
                status_code=422,
                detail=f"'{field_name}' is required and cannot be empty.",
            )

    notif_enabled = (
        receive_notifications
        if isinstance(receive_notifications, bool)
        else str(receive_notifications).strip().lower() in {"true", "1", "yes", "on"}
    )

    if "@" not in auth_person_email or "." not in auth_person_email.split("@")[-1]:
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid authorised person email ('auth_person_email').",
        )

    cleaned_additional_email = (
        additional_email.strip()
        if additional_email and additional_email.strip()
        else None
    )
    if notif_enabled and cleaned_additional_email:
        if (
            "@" not in cleaned_additional_email
            or "." not in cleaned_additional_email.split("@")[-1]
        ):
            raise HTTPException(
                status_code=422,
                detail="Please provide a valid additional email address ('additional_email').",
            )

    start = _parse_iso_date(start_date, "start_date")
    end = _parse_iso_date(end_date, "end_date")
    if end < start:
        raise HTTPException(
            status_code=422,
            detail="end_date cannot be earlier than start_date.",
        )

    cleaned_budget = budget.replace("₹", "").replace("$", "").replace(",", "").strip()
    try:
        budget_value = Decimal(cleaned_budget)
        if (
            not budget_value.is_finite()
            or budget_value <= 0
            or budget_value.as_tuple().exponent < -2
            or budget_value >= Decimal("10000000000000")
        ):
            raise ValueError
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=422,
            detail=f"'budget' ('{budget}') must be a positive number with at most 2 decimal places.",
        )

    file_bytes: bytes | None = None
    if sow_file is not None and sow_file.filename:
        extension = (
            "." + sow_file.filename.rsplit(".", 1)[-1].lower()
            if "." in sow_file.filename
            else ""
        )
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '{extension}'. Allowed: JPG, JPEG, PNG, PDF, DOC, DOCX, XLS, XLSX, CSV, ZIP.",
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

    try:
        project = create_project(
            db,
            customer_id=customer_id.strip(),
            title=title.strip(),
            description=description.strip(),
            project_is=(project_is or "New").strip(),
            project_type=(project_type or "General").strip(),
            category=(category or "General").strip(),
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            currency=_normalize_currency(currency),
            budget=budget_value,
            auth_person_name=auth_person_name.strip(),
            auth_person_email=auth_person_email.strip(),
            contact_number=contact_number.strip(),
            sow_file=file_bytes,
            receive_notifications=notif_enabled,
            additional_email=cleaned_additional_email,
            promo_code=promo_code.strip() if promo_code and promo_code.strip() else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save project: {exc}",
        )

    return {
        "success": True,
        "message": "Project uploaded successfully.",
        "project": {
            "id": project.plist_id,
            "projectId": project.plist_projectid,
            "title": project.plist_title,
            "status": project.plist_status,
            "projectStatus": project.plist_project_status,
            "customerId": project.plist_customer_id,
            "startDate": project.plist_startdate,
            "endDate": project.plist_enddate,
            "sowUploaded": project.plist_sow is not None,
        },
    }
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.project import Project


def generate_project_id(db: Session, current_time: datetime) -> str:
    """
    Generates a unique Project ID matching the legacy Laravel format:
    'Pseudo-YYYY-MMDDHHMMSS' (e.g. 'Pseudo-2026-0923173109').
    """
    base_id = f"Pseudo-{current_time.strftime('%Y-%m%d%H%M%S')}"
    candidate_id = base_id
    counter = 1

    # Guard against two projects created within the exact same second
    while db.query(Project).filter(Project.plist_projectid == candidate_id).first():
        candidate_id = f"{base_id}-{counter}"
        counter += 1

    return candidate_id


def create_project(
    db: Session,
    *,
    customer_id: str,
    title: str,
    description: str,
    project_is: str,
    project_type: str,
    category: str,
    start_date: str,
    end_date: str,
    currency: str,
    budget: Decimal,
    auth_person_name: str,
    auth_person_email: str,
    contact_number: str,
    sow_file: bytes | None,
    receive_notifications: bool = False,
    additional_email: str | None = None,
    promo_code: str | None = None,
) -> Project:
    # Match Laravel's Asia/Kolkata timezone and formatting
    ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    project_id = generate_project_id(db, ist_now)

    # Match Laravel date & timestamp formats (dd-mm-YYYY and dd-mm-YYYY HH:MM:SS)
    formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    current_timestamp = ist_now.strftime("%d-%m-%Y %H:%M:%S")

    project = Project(
        plist_customer_id=customer_id,
        plist_projectid=project_id,
        plist_title=title,
        plist_description=description,
        plist_sow=sow_file,
        plist_type=project_type,

        # Nullable location columns
        plist_country=None,
        plist_state=None,
        plist_city=None,
        plist_pincode=None,

        plist_startdate=formatted_start_date,
        plist_enddate=formatted_end_date,
        plist_currency=currency,
        plist_budget=budget,
        plist_final_price=None,

        # Authorised contact information
        plist_name=auth_person_name,
        plist_email=auth_person_email,
        plist_contact=contact_number,

        # Legacy Laravel initial statuses & dropdown selections
        plist_status="No SP Assigned",
        plist_project_status="Live",
        plist_ongnew=project_is,
        plist_category=category,
        plist_coupon=promo_code or None,

        # Notification fields matched to Laravel ('True' / 'False')
        plist_checkrcv="True" if receive_notifications else "False",
        plist_customeremail=additional_email if receive_notifications else None,

        # Remaining nullable fields
        plist_payment_id=None,
        plist_delivered_on=None,
        plist_payment_on=None,
        plist_project_status_description=None,
        plist_pt_mngr_id=None,
        plist_emp_code=None,

        created_at=current_timestamp,
        updated_at=current_timestamp,
    )

    try:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    except Exception:
        db.rollback()
        raise
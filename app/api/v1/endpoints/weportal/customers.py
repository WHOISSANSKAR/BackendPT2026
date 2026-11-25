from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser

router = APIRouter()

POWN_ID_COL = getattr(ProjectOwner, "pown_id", None) or getattr(ProjectOwner, "id")
POWN_NAME_COL = (
    getattr(ProjectOwner, "pown_name", None)
    or getattr(ProjectOwner, "name", None)
)
POWN_USERNAME_COL = (
    getattr(ProjectOwner, "pown_username", None)
    or getattr(ProjectOwner, "username", None)
)
POWN_ORG_COL = (
    getattr(ProjectOwner, "pown_organisation_name", None)
    or getattr(ProjectOwner, "pown_organization_name", None)
    or getattr(ProjectOwner, "organisation_name", None)
)
POWN_EMAIL_COL = (
    getattr(ProjectOwner, "pown_email", None)
    or getattr(ProjectOwner, "email", None)
)
POWN_CONTACT_COL = (
    getattr(ProjectOwner, "pown_contact", None)
    or getattr(ProjectOwner, "contact", None)
)


@router.get("/customers/dropdown")
def get_weportal_customer_dropdown(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    """
    Returns customers for the Upload Project dropdown.
    `pown_id` maps to `project_list.plist_customer_id`, and `pown_name` is the customer name.
    """
    select_cols = [
        POWN_ID_COL.label("pown_id"),
        (
            POWN_NAME_COL.label("pown_name")
            if POWN_NAME_COL is not None
            else func.cast(None, POWN_ID_COL.type).label("pown_name")
        ),
        (
            POWN_USERNAME_COL.label("pown_username")
            if POWN_USERNAME_COL is not None
            else func.cast(None, POWN_ID_COL.type).label("pown_username")
        ),
        (
            POWN_ORG_COL.label("pown_organisation_name")
            if POWN_ORG_COL is not None
            else func.cast(None, POWN_ID_COL.type).label("pown_organisation_name")
        ),
        (
            POWN_EMAIL_COL.label("pown_email")
            if POWN_EMAIL_COL is not None
            else func.cast(None, POWN_ID_COL.type).label("pown_email")
        ),
        (
            POWN_CONTACT_COL.label("pown_contact")
            if POWN_CONTACT_COL is not None
            else func.cast(None, POWN_ID_COL.type).label("pown_contact")
        ),
    ]

    stmt = select(*select_cols)

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        search_filters = []
        if POWN_NAME_COL is not None:
            search_filters.append(POWN_NAME_COL.ilike(pattern))
        if POWN_USERNAME_COL is not None:
            search_filters.append(POWN_USERNAME_COL.ilike(pattern))
        if POWN_ORG_COL is not None:
            search_filters.append(POWN_ORG_COL.ilike(pattern))
        if search_filters:
            stmt = stmt.where(or_(*search_filters))

    order_col = POWN_NAME_COL if POWN_NAME_COL is not None else POWN_ID_COL
    rows = db.execute(stmt.order_by(order_col.asc(), POWN_ID_COL.asc())).all()

    customers = []
    for row in rows:
        customer_name = (
            row.pown_name
            or row.pown_organisation_name
            or row.pown_username
            or f"Customer #{row.pown_id}"
        )
        username_part = f" ({row.pown_username})" if row.pown_username else ""
        label = f"{customer_name}{username_part} (#{row.pown_id})"

        customers.append(
            {
                "id": row.pown_id,
                "pown_id": row.pown_id,
                "pown_name": customer_name,
                "name": customer_name,
                "pown_username": row.pown_username,
                "pown_organisation_name": row.pown_organisation_name,
                "pown_email": row.pown_email,
                "pown_contact": row.pown_contact,
                "label": label,
            }
        )

    return {
        "success": True,
        "total": len(customers),
        "customers": customers,
        "items": customers,
    }
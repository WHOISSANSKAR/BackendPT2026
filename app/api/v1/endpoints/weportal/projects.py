from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, case, cast, func, Integer, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser

router = APIRouter()

MYSQL_COLLATION = "utf8mb4_general_ci"

PROJECTS_PAGE_ALLOWED_STATUSES = (
    "in progress",
    "on hold",
    "no sp assigned",
    "not started",
)


class WePortalProjectUpdateRequest(BaseModel):
    customer_id: str | None = None
    title: str | None = None
    description: str | None = None
    project_is: str | None = None
    project_type: str | None = None
    project_category: str | None = None
    currency: str | None = None
    budget: float | int | str | None = None
    start_date: str | None = None
    end_date: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    notification_email: str | None = None
    promo_code: str | None = None
    final_price: float | int | str | None = None
    status: str | None = None
    delivered_on: str | None = None
    project_status: str | None = None
    project_status_description: str | None = None
    assign_to: str | None = None
    manager_id: str | int | None = None
    employee_code: str | None = None


def _norm_str(col):
    return func.lower(func.trim(func.coalesce(col, ""))).collate(MYSQL_COLLATION)


def _workflow_status_norm():
    return _norm_str(func.coalesce(Project.plist_status, "No SP Assigned"))


def _customer_join_condition():
    cust_trimmed = func.trim(func.coalesce(Project.plist_customer_id, ""))
    numeric_cust_id = case(
        (cust_trimmed.op("REGEXP")("^[0-9]+$"), cast(cust_trimmed, Integer)),
        else_=None,
    )
    cust_norm = _norm_str(Project.plist_customer_id)
    return or_(
        ProjectOwner.pown_id == numeric_cust_id,
        and_(
            cust_norm != "",
            _norm_str(ProjectOwner.pown_username) == cust_norm,
        ),
    )


def _manager_join_condition():
    mgr_trimmed = func.trim(func.coalesce(Project.plist_pt_mngr_id, ""))
    numeric_mgr_id = case(
        (mgr_trimmed.op("REGEXP")("^[0-9]+$"), cast(mgr_trimmed, Integer)),
        else_=None,
    )
    mgr_norm = _norm_str(Project.plist_pt_mngr_id)
    return or_(
        WeUser.id == numeric_mgr_id,
        and_(
            mgr_norm != "",
            _norm_str(WeUser.username) == mgr_norm,
        ),
        and_(
            mgr_norm != "",
            _norm_str(WeUser.emp_code) == mgr_norm,
        ),
    )


def _parse_decimal_or_none(val: float | int | str | None):
    if val is None:
        return None
    if isinstance(val, str):
        cleaned = val.replace("₹", "").replace("$", "").replace(",", "").strip()
        if cleaned == "":
            return None
        return float(cleaned)
    return float(val)


def _serialize_project(
    proj: Project,
    pown_name: str | None = None,
    pown_username: str | None = None,
    pown_org_name: str | None = None,
    mgr_id: int | None = None,
    mgr_username: str | None = None,
    mgr_email: str | None = None,
) -> dict:
    budget_val = (
        float(proj.plist_budget) if proj.plist_budget is not None else None
    )
    final_price_val = (
        float(proj.plist_final_price)
        if proj.plist_final_price is not None
        else None
    )
    has_sow = bool(proj.plist_sow)

    mgr_label = None
    if mgr_username or mgr_email or mgr_id is not None:
        parts = [p for p in [mgr_username, mgr_email] if p]
        suffix = f" ({mgr_id})" if mgr_id is not None else ""
        mgr_label = f"{' - '.join(parts)}{suffix}".strip() or str(mgr_id)

    raw_mgr_str = (proj.plist_pt_mngr_id or "").strip()
    is_unassigned_mgr = raw_mgr_str in ("", "0", "None", "none", "null", "unassigned")
    manager_display = None if is_unassigned_mgr else (mgr_label or raw_mgr_str)

    workflow_status = (proj.plist_status or "No SP Assigned").strip()
    lifecycle_project_status = (proj.plist_project_status or "Live").strip()

    customer_label = (
        pown_name or pown_org_name or pown_username or proj.plist_name or None
    )

    resolved_mgr_id = (
        mgr_id
        if mgr_id is not None
        else (int(raw_mgr_str) if raw_mgr_str.isdigit() and raw_mgr_str != "0" else None)
    )

    return {
        "id": str(proj.plist_id),
        "plist_id": proj.plist_id,
        "code": proj.plist_projectid,
        "title": proj.plist_title,
        "description": proj.plist_description,
        "customer": customer_label,
        "customer_id": proj.plist_customer_id,
        "customer_username": pown_username,
        "customer_organisation": pown_org_name,
        "has_sow": has_sow,
        "scope_of_work_file_name": (
            f"{proj.plist_projectid or proj.plist_id}_SOW" if has_sow else None
        ),
        "project_is": proj.plist_ongnew,
        "project_type": proj.plist_type,
        "project_category": proj.plist_category,
        "currency": proj.plist_currency,
        "amount": budget_val,
        "budget": budget_val,
        "final_price": final_price_val,
        "start_date": proj.plist_startdate,
        "end_date": proj.plist_enddate,
        "contact_name": proj.plist_name,
        "contact_email": proj.plist_email,
        "contact_phone": proj.plist_contact,
        "notification_email": proj.plist_customeremail,
        "promo_code": proj.plist_coupon,
        "status": workflow_status,
        "assignment_status": workflow_status,
        "project_status": lifecycle_project_status,
        "delivered_on": proj.plist_delivered_on,
        "project_status_description": proj.plist_project_status_description,
        "manager_id": resolved_mgr_id,
        "sp": manager_display,
        "assign_to": manager_display,
        "employee_code": proj.plist_emp_code,
    }


@router.get("/managers/list")
def list_weportal_managers(
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    rows = db.execute(
        select(
            WeUser.id,
            WeUser.username,
            WeUser.email,
            WeUser.emp_code,
        ).order_by(WeUser.username.asc())
    ).all()

    managers = [
        {
            "id": r.id,
            "user_id": r.id,
            "username": r.username,
            "email": r.email,
            "emp_code": r.emp_code,
            "label": f"{r.username or ''} ({r.email or ''}) ({r.id})".strip(),
        }
        for r in rows
    ]
    return {"success": True, "total": len(managers), "managers": managers}


@router.get("")
def list_weportal_active_projects(
    search: str | None = Query(default=None),
    project_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    """
    Projects page list:
    Includes 'In Progress', 'On Hold', and 'No SP Assigned' (Not Started),
    regardless of manager assignment, and strictly excludes 'Delivered'.
    """
    workflow_status_expr = _workflow_status_norm()

    conditions = [
        workflow_status_expr != "delivered",
        workflow_status_expr.in_(PROJECTS_PAGE_ALLOWED_STATUSES),
    ]

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                Project.plist_projectid.ilike(pattern),
                Project.plist_title.ilike(pattern),
                ProjectOwner.pown_name.ilike(pattern),
                ProjectOwner.pown_organisation_name.ilike(pattern),
                WeUser.username.ilike(pattern),
            )
        )

    if (
        project_status
        and project_status.strip()
        and project_status.strip().lower() != "all"
    ):
        requested = project_status.strip().lower()
        if requested == "delivered":
            conditions.append(workflow_status_expr == "__none__")
        else:
            conditions.append(workflow_status_expr == requested)

    rows = db.execute(
        select(
            Project,
            ProjectOwner.pown_name,
            ProjectOwner.pown_username,
            ProjectOwner.pown_organisation_name,
            WeUser.id.label("mgr_id"),
            WeUser.username.label("mgr_username"),
            WeUser.email.label("mgr_email"),
        )
        .outerjoin(ProjectOwner, _customer_join_condition())
        .outerjoin(WeUser, _manager_join_condition())
        .where(and_(*conditions))
        .order_by(Project.plist_id.desc())
    ).all()

    items = [
        _serialize_project(
            proj,
            pown_name=pown_name,
            pown_username=pown_username,
            pown_org_name=pown_org_name,
            mgr_id=mgr_id,
            mgr_username=mgr_username,
            mgr_email=mgr_email,
        )
        for proj, pown_name, pown_username, pown_org_name, mgr_id, mgr_username, mgr_email in rows
    ]

    return {
        "success": True,
        "total": len(items),
        "items": items,
        "projects": items,
    }


@router.get("/{project_ref}")
def get_weportal_project_detail(
    project_ref: str = Path(..., description="Project plist_id or plist_projectid"),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    ref = project_ref.strip()
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project reference",
        )

    filters = [Project.plist_projectid == ref]
    if ref.isdigit():
        filters.append(Project.plist_id == int(ref))

    row = db.execute(
        select(
            Project,
            ProjectOwner.pown_name,
            ProjectOwner.pown_username,
            ProjectOwner.pown_organisation_name,
            WeUser.id.label("mgr_id"),
            WeUser.username.label("mgr_username"),
            WeUser.email.label("mgr_email"),
        )
        .outerjoin(ProjectOwner, _customer_join_condition())
        .outerjoin(WeUser, _manager_join_condition())
        .where(or_(*filters))
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    proj, pown_name, pown_username, pown_org_name, mgr_id, mgr_username, mgr_email = row

    return {
        "success": True,
        "project": _serialize_project(
            proj,
            pown_name=pown_name,
            pown_username=pown_username,
            pown_org_name=pown_org_name,
            mgr_id=mgr_id,
            mgr_username=mgr_username,
            mgr_email=mgr_email,
        ),
    }


@router.patch("/{project_ref}")
def update_weportal_project_detail(
    payload: WePortalProjectUpdateRequest,
    project_ref: str = Path(..., description="Project plist_id or plist_projectid"),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    ref = project_ref.strip()
    filters = [Project.plist_projectid == ref]
    if ref.isdigit():
        filters.append(Project.plist_id == int(ref))

    proj = db.execute(select(Project).where(or_(*filters))).scalar_one_or_none()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if payload.customer_id is not None:
        proj.plist_customer_id = payload.customer_id.strip()
    if payload.title is not None:
        proj.plist_title = payload.title.strip()
    if payload.description is not None:
        proj.plist_description = payload.description.strip()
    if payload.project_is is not None:
        proj.plist_ongnew = payload.project_is.strip()
    if payload.project_type is not None:
        proj.plist_type = payload.project_type.strip()
    if payload.project_category is not None:
        proj.plist_category = payload.project_category.strip()
    if payload.currency is not None:
        proj.plist_currency = payload.currency.strip().upper()
    if payload.budget is not None:
        parsed_budget = _parse_decimal_or_none(payload.budget)
        if parsed_budget is not None:
            proj.plist_budget = parsed_budget
    if payload.start_date is not None:
        proj.plist_startdate = payload.start_date.strip()
    if payload.end_date is not None:
        proj.plist_enddate = payload.end_date.strip()
    if payload.contact_name is not None:
        proj.plist_name = payload.contact_name.strip()
    if payload.contact_email is not None:
        proj.plist_email = payload.contact_email.strip()
    if payload.contact_phone is not None:
        proj.plist_contact = payload.contact_phone.strip()
    if payload.notification_email is not None:
        proj.plist_customeremail = payload.notification_email.strip() or None
    if payload.promo_code is not None:
        proj.plist_coupon = payload.promo_code.strip() or None
    if payload.final_price is not None:
        proj.plist_final_price = _parse_decimal_or_none(payload.final_price)
    if payload.status is not None:
        proj.plist_status = payload.status.strip()
    if payload.delivered_on is not None:
        proj.plist_delivered_on = payload.delivered_on.strip() or None
    if payload.project_status is not None:
        proj.plist_project_status = payload.project_status.strip() or None
    if payload.project_status_description is not None:
        proj.plist_project_status_description = (
            payload.project_status_description.strip() or None
        )

    mgr_raw = (
        payload.manager_id if payload.manager_id is not None else payload.assign_to
    )
    if mgr_raw is not None:
        mgr_str = str(mgr_raw).strip()
        proj.plist_pt_mngr_id = (
            None
            if mgr_str.lower() in ("", "0", "none", "null", "unassigned")
            else mgr_str
        )

    if payload.employee_code is not None:
        proj.plist_emp_code = payload.employee_code.strip() or None

    db.commit()
    db.refresh(proj)

    updated_row = db.execute(
        select(
            Project,
            ProjectOwner.pown_name,
            ProjectOwner.pown_username,
            ProjectOwner.pown_organisation_name,
            WeUser.id.label("mgr_id"),
            WeUser.username.label("mgr_username"),
            WeUser.email.label("mgr_email"),
        )
        .outerjoin(ProjectOwner, _customer_join_condition())
        .outerjoin(WeUser, _manager_join_condition())
        .where(Project.plist_id == proj.plist_id)
    ).first()

    u_proj, pown_name, pown_username, pown_org_name, mgr_id, mgr_username, mgr_email = updated_row

    return {
        "success": True,
        "message": "Project updated successfully.",
        "project": _serialize_project(
            u_proj,
            pown_name=pown_name,
            pown_username=pown_username,
            pown_org_name=pown_org_name,
            mgr_id=mgr_id,
            mgr_username=mgr_username,
            mgr_email=mgr_email,
        ),
    }
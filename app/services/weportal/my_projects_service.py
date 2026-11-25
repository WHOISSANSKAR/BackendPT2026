from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, cast, func, Integer, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser
from app.schemas.weportal.my_projects import (
    WePortalMyProjectItem,
    WePortalMyProjectsResponse,
)

router = APIRouter()

MYSQL_COLLATION = "utf8mb4_general_ci"


def _norm_str(col):
    return func.lower(func.trim(func.coalesce(col, ""))).collate(MYSQL_COLLATION)


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


def _assigned_to_current_manager_condition(current_user: WeUser):
    """
    Matches projects assigned to the logged-in manager across all statuses,
    including 'No SP Assigned' and 'In Progress'.
    """
    mgr_trimmed = func.trim(func.coalesce(Project.plist_pt_mngr_id, ""))
    mgr_norm = _norm_str(Project.plist_pt_mngr_id)

    match_clauses = [mgr_trimmed == str(current_user.id)]

    if current_user.username and current_user.username.strip():
        match_clauses.append(mgr_norm == current_user.username.strip().lower())

    emp_code = getattr(current_user, "emp_code", None)
    if emp_code and str(emp_code).strip():
        match_clauses.append(mgr_norm == str(emp_code).strip().lower())

    return and_(
        mgr_trimmed != "",
        ~mgr_norm.in_(("", "0", "none", "null", "unassigned")),
        or_(*match_clauses),
    )


@router.get("", response_model=WePortalMyProjectsResponse)
def list_my_weportal_projects(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    conditions = [_assigned_to_current_manager_condition(current_user)]

    if (
        status_filter
        and status_filter.strip()
        and status_filter.strip().lower() != "all"
    ):
        conditions.append(
            _norm_str(func.coalesce(Project.plist_status, "No SP Assigned"))
            == status_filter.strip().lower()
        )

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                Project.plist_projectid.ilike(pattern),
                Project.plist_title.ilike(pattern),
                Project.plist_description.ilike(pattern),
                ProjectOwner.pown_name.ilike(pattern),
                ProjectOwner.pown_organisation_name.ilike(pattern),
            )
        )

    rows = db.execute(
        select(
            Project.plist_id,
            Project.plist_customer_id,
            ProjectOwner.pown_id,
            ProjectOwner.pown_name,
            ProjectOwner.pown_username,
            ProjectOwner.pown_user_type,
            ProjectOwner.pown_organisation_name,
            Project.plist_projectid,
            Project.plist_title,
            Project.plist_description,
            Project.plist_startdate,
            Project.plist_enddate,
            Project.plist_status,
        )
        .outerjoin(ProjectOwner, _customer_join_condition())
        .where(and_(*conditions))
        .order_by(Project.plist_id.desc())
    ).all()

    items = [
        WePortalMyProjectItem(
            plist_id=row.plist_id,
            plist_customer_id=(
                int(row.plist_customer_id)
                if row.plist_customer_id
                and str(row.plist_customer_id).strip().isdigit()
                else None
            ),
            pown_id=row.pown_id,
            pown_name=row.pown_name,
            pown_username=row.pown_username,
            pown_user_type=row.pown_user_type,
            pown_organisation_name=row.pown_organisation_name,
            plist_projectid=row.plist_projectid,
            plist_title=row.plist_title,
            plist_description=row.plist_description,
            plist_startdate=row.plist_startdate,
            plist_enddate=row.plist_enddate,
            plist_status=row.plist_status or "No SP Assigned",
        )
        for row in rows
    ]

    return WePortalMyProjectsResponse(
        success=True,
        total=len(items),
        projects=items,
    )
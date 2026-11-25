from sqlalchemy import and_, case, cast, func, Integer, or_, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser
from app.schemas.weportal.dashboard import (
    WePortalDashboardCounts,
    WePortalDashboardResponse,
    WePortalRecentProject,
)

MYSQL_COLLATION = "utf8mb4_general_ci"

POWN_ID_COL = getattr(ProjectOwner, "pown_id", None) or getattr(ProjectOwner, "id")
POWN_NAME_COL = getattr(ProjectOwner, "pown_name", None) or getattr(ProjectOwner, "name", None)
POWN_USERNAME_COL = getattr(ProjectOwner, "pown_username", None) or getattr(ProjectOwner, "username", None)
POWN_ORG_COL = (
    getattr(ProjectOwner, "pown_organisation_name", None)
    or getattr(ProjectOwner, "pown_organization_name", None)
    or getattr(ProjectOwner, "organisation_name", None)
)


def _norm_str(col):
    return func.lower(func.trim(func.coalesce(col, ""))).collate(MYSQL_COLLATION)


def _customer_join_condition():
    cust_trimmed = func.trim(func.coalesce(Project.plist_customer_id, ""))
    numeric_cust_id = case(
        (cust_trimmed.op("REGEXP")("^[0-9]+$"), cast(cust_trimmed, Integer)),
        else_=None,
    )
    cust_norm = _norm_str(Project.plist_customer_id)
    clauses = [POWN_ID_COL == numeric_cust_id]
    if POWN_USERNAME_COL is not None:
        clauses.append(
            and_(
                cust_norm != "",
                _norm_str(POWN_USERNAME_COL) == cust_norm,
            )
        )
    return or_(*clauses)


def _unassigned_manager_condition():
    mgr_norm = _norm_str(Project.plist_pt_mngr_id)
    return mgr_norm.in_(("", "0", "none", "null", "unassigned"))


def _no_sp_assigned_condition():
    return _norm_str(Project.plist_status) == "no sp assigned"


def _parse_optional_int(val) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    return int(s) if s.isdigit() else None


def get_weportal_dashboard_data(
    db: Session,
    current_user: WeUser,
) -> WePortalDashboardResponse:
    project_list_count = (
        db.execute(select(func.count(Project.plist_id))).scalar() or 0
    )
    project_owners_count = (
        db.execute(select(func.count(POWN_ID_COL))).scalar() or 0
    )

    select_cols = [
        Project.plist_id,
        Project.plist_customer_id,
        POWN_ID_COL.label("owner_pk"),
        (POWN_NAME_COL if POWN_NAME_COL is not None else func.cast(None, Project.plist_title.type)).label("owner_name"),
        (POWN_USERNAME_COL if POWN_USERNAME_COL is not None else func.cast(None, Project.plist_title.type)).label("owner_username"),
        (POWN_ORG_COL if POWN_ORG_COL is not None else func.cast(None, Project.plist_title.type)).label("owner_org"),
        Project.plist_projectid,
        Project.plist_title,
        Project.plist_description,
        Project.plist_startdate,
        Project.plist_enddate,
        Project.plist_status,
    ]

    recent_project_rows = db.execute(
        select(*select_cols)
        .outerjoin(ProjectOwner, _customer_join_condition())
        .where(
            and_(
                _no_sp_assigned_condition(),
                _unassigned_manager_condition(),
            )
        )
        .order_by(Project.plist_id.desc())
        .limit(10)
    ).all()

    recent_projects = [
        WePortalRecentProject(
            plist_id=row.plist_id,
            plist_customer_id=(
                row.owner_pk
                if row.owner_pk is not None
                else _parse_optional_int(row.plist_customer_id)
            ),
            customer_name=(
                row.owner_name
                or row.owner_org
                or row.owner_username
            ),
            plist_projectid=row.plist_projectid,
            plist_title=row.plist_title,
            plist_description=row.plist_description,
            plist_startdate=row.plist_startdate,
            plist_enddate=row.plist_enddate,
            plist_status=row.plist_status or "No SP Assigned",
        )
        for row in recent_project_rows
    ]

    counts = WePortalDashboardCounts(
        project_owners=project_owners_count,
        service_providers=0,
        project_list=project_list_count,
        project_list_by_admin=0,
        hardwares=0,
        orders_pending=0,
        orders_placed=0,
        tickets_count=0,
        unread_notifications_count=0,
        hardware_orders_count=0,
    )

    return WePortalDashboardResponse(
        success=True,
        counts=counts,
        recent_projects=recent_projects,
        notifications=[],
    )
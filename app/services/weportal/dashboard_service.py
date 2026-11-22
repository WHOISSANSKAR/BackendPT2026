# app/services/weportal/dashboard_service.py
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.hardware import Hardware
from app.models.order_placed import OrderPlaced
from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.ticket import Ticket
from app.models.user import User
from app.models.weuser import WeUser
from app.schemas.weportal.dashboard import (
    WePortalDashboardCounts,
    WePortalDashboardResponse,
    WePortalRecentProject,
)


def get_weportal_dashboard_data(
    db: Session,
    current_user: WeUser,
) -> WePortalDashboardResponse:
    # 1. Customers count
    project_owners = db.scalar(select(func.count(ProjectOwner.pown_id))) or 0

    # 2. ASPs (Service Providers) count
    service_providers = (
        db.scalar(
            select(func.count(User.id)).where(
                func.lower(User.user_type).in_(["partner", "asp", "service_provider"])
            )
        )
        or 0
    )

    # 3. Total Projects count
    project_list = db.scalar(select(func.count(Project.plist_id))) or 0

    # 4. My Projects count (assigned to current WePortal user by ID or emp_code)
    my_project_filters = [Project.plist_pt_mngr_id == str(current_user.id)]
    if current_user.emp_code:
        my_project_filters.append(Project.plist_emp_code == current_user.emp_code)

    project_list_by_admin = (
        db.scalar(
            select(func.count(Project.plist_id)).where(or_(*my_project_filters))
        )
        or 0
    )

    # 5. Hardwares count
    hardwares = db.scalar(select(func.count(Hardware.hrdws_id))) or 0

    # 6. Pending Orders vs Placed Orders (from orders_placed)
    orders_pending = (
        db.scalar(
            select(func.count(OrderPlaced.ordplcd_id)).where(
                func.lower(OrderPlaced.ordplcd_status) == "pending"
            )
        )
        or 0
    )
    orders_placed = db.scalar(select(func.count(OrderPlaced.ordplcd_id))) or 0

    # 7. Tickets count
    tickets_count = db.scalar(select(func.count(Ticket.tckt_id))) or 0

    counts = WePortalDashboardCounts(
        project_owners=project_owners,
        service_providers=service_providers,
        project_list=project_list,
        project_list_by_admin=project_list_by_admin,
        hardwares=hardwares,
        orders_pending=orders_pending,
        orders_placed=orders_placed,
        tickets_count=tickets_count,
    )

    # 8. Recent Projects (matching your PHP query: plist_status = 'NO SP Assigned')
    rows = db.scalars(
        select(Project)
        .where(Project.plist_status == "NO SP Assigned")
        .order_by(Project.plist_id.desc())
    ).all()

    recent_projects = [
        WePortalRecentProject(
            plist_id=row.plist_id,
            plist_customer_id=int(row.plist_customer_id)
            if row.plist_customer_id and row.plist_customer_id.isdigit()
            else None,
            plist_projectid=row.plist_projectid,
            plist_title=row.plist_title,
            plist_description=row.plist_description,
            plist_startdate=row.plist_startdate,
            plist_enddate=row.plist_enddate,
            plist_status=row.plist_status,
        )
        for row in rows
    ]

    return WePortalDashboardResponse(
        success=True,
        counts=counts,
        recent_projects=recent_projects,
    )
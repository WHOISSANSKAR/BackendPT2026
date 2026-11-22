from sqlalchemy import cast, func, or_, select, String
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.weuser import WeUser
from app.schemas.weportal.my_projects import MyProjectItemOut, MyProjectsResponse


def get_my_projects(
    db: Session,
    current_user: WeUser,
    search: str | None = None,
    status: str | None = None,
) -> MyProjectsResponse:
    stmt = (
        select(
            Project,
            ProjectOwner.pown_id,
            ProjectOwner.pown_name,
            ProjectOwner.pown_username,
            ProjectOwner.pown_user_type,
            ProjectOwner.pown_organisation_name,
        )
        .outerjoin(
            ProjectOwner,
            cast(ProjectOwner.pown_id, String) == Project.plist_customer_id,
        )
        .where(
            Project.plist_pt_mngr_id == str(current_user.id),
            func.lower(func.coalesce(Project.plist_status, "")) != "delivered",
        )
        .order_by(Project.plist_id.desc())
    )

    if status and status.strip() and status.strip().lower() != "all":
        stmt = stmt.where(Project.plist_status == status.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Project.plist_projectid.ilike(term),
                Project.plist_title.ilike(term),
                Project.plist_status.ilike(term),
                ProjectOwner.pown_name.ilike(term),
                ProjectOwner.pown_organisation_name.ilike(term),
            )
        )

    rows = db.execute(stmt).all()

    items: list[MyProjectItemOut] = []
    for proj, pown_id, pown_name, pown_username, pown_user_type, pown_org in rows:
        items.append(
            MyProjectItemOut(
                plist_id=proj.plist_id,
                plist_customer_id=int(proj.plist_customer_id)
                if proj.plist_customer_id and proj.plist_customer_id.isdigit()
                else None,
                plist_projectid=proj.plist_projectid,
                plist_title=proj.plist_title,
                plist_description=proj.plist_description,
                plist_startdate=proj.plist_startdate,
                plist_enddate=proj.plist_enddate,
                plist_status=proj.plist_status,
                plist_pt_mngr_id=proj.plist_pt_mngr_id,
                plist_emp_code=proj.plist_emp_code,
                pown_id=pown_id,
                pown_name=pown_name or proj.plist_name,
                pown_username=pown_username,
                pown_user_type=pown_user_type,
                pown_organisation_name=pown_org,
            )
        )

    return MyProjectsResponse(
        success=True,
        items=items,
        total=len(items),
    )
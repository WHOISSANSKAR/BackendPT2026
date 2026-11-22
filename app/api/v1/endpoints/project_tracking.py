
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.models.project import Project
from app.models.project_owner import ProjectOwner

from app.services.project_tracking_service import (
    get_customer_tracking_projects,
    get_project_tracking,
)


router = APIRouter()


@router.get("/projects/tracking")
def customer_tracking_projects(
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    customer_id = str(current_customer.pown_id)

    return get_customer_tracking_projects(
        db=db,
        customer_id=customer_id,
    )


@router.get("/projects/{project_id}/tracking")
def customer_project_tracking(
    project_id: int,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    customer_id = str(current_customer.pown_id)

    project = (
        db.query(Project)
        .filter(
            Project.plist_id == project_id,
            Project.plist_customer_id == customer_id,
            Project.plist_status != "Delivered",
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = get_project_tracking(
        db=db,
        project=project,
    )

    # Use the logged-in Project Owner's name instead of plist_name
    result["project"]["customer_name"] = current_customer.pown_name

    return result

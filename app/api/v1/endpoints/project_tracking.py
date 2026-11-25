from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.models.project import Project
from app.models.project_owner import ProjectOwner

from app.services.project_tracking_service import (
    get_customer_tracking_projects,
    get_project_tracking,
    get_task_poc_blob_payload,
)


router = APIRouter()


@router.get("/projects/tracking")
def customer_tracking_projects(
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
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
    current_customer: ProjectOwner = Depends(get_current_customer),
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

    result["project"]["customer_name"] = current_customer.pown_name
    return result


@router.get("/projects/{project_id}/tasks/{task_id}/poc")
def get_task_proof_of_completion(
    project_id: int,
    task_id: int,
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    payload = get_task_poc_blob_payload(
        db=db,
        project_id=project_id,
        customer_id=str(current_customer.pown_id),
        task_id=task_id,
    )

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Approved Proof of Completion not available for this task.",
        )

    raw_bytes, media_type, filename = payload
    disposition = "attachment" if download else "inline"

    return Response(
        content=raw_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.weportal.tasks import MilestoneTaskCreate, MilestoneTaskUpdate
from app.services.weportal import tasks_service as task_service

router = APIRouter(
    prefix="/weportal",
    tags=["WePortal Tasks"],
)


@router.get(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks/weightage-sum"
)
def get_milestone_task_weightage_sum(
    project_id: int,
    location_id: int,
    milestone_id: int,
    pptasks_id: Optional[int] = Query(default=None),
    entered_weightage: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    return task_service.get_task_weightage_sum(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        exclude_task_id=pptasks_id,
        entered_weightage=entered_weightage,
    )


@router.get(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks"
)
def list_milestone_tasks(
    project_id: int,
    location_id: int,
    milestone_id: int,
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    tasks = task_service.list_milestone_tasks(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        search=search,
    )
    return {
        "success": True,
        "total": len(tasks),
        "tasks": tasks,
    }


@router.post(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks",
    status_code=status.HTTP_201_CREATED,
)
def create_milestone_task(
    project_id: int,
    location_id: int,
    milestone_id: int,
    payload: MilestoneTaskCreate,
    db: Session = Depends(get_db),
):
    task = task_service.create_milestone_task(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        payload=payload,
    )
    return {
        "success": True,
        "task": task,
        **task,
    }


@router.post(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks/import",
    status_code=status.HTTP_201_CREATED,
)
def import_milestone_tasks(
    project_id: int,
    location_id: int,
    milestone_id: int,
    excel_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = (excel_file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload an .xlsx, .xls, or .csv file.",
        )

    result = task_service.import_milestone_tasks_file(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        upload_file=excel_file,
    )
    return {
        "success": True,
        "message": result.get("message", "Tasks imported successfully."),
        "imported_count": result.get("imported_count", 0),
        "tasks": result.get("tasks", []),
    }


@router.patch(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks/{task_id}"
)
def update_milestone_task(
    project_id: int,
    location_id: int,
    milestone_id: int,
    task_id: int,
    payload: MilestoneTaskUpdate,
    db: Session = Depends(get_db),
):
    task = task_service.update_milestone_task(
        db=db,
        milestone_id=milestone_id,
        task_id=task_id,
        payload=payload,
        project_id=project_id,
        location_id=location_id,
    )
    return {
        "success": True,
        "task": task,
        **task,
    }


@router.delete(
    "/projects/{project_id}/locations/{location_id}/milestones/{milestone_id}/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
)
def delete_milestone_task(
    project_id: int,
    location_id: int,
    milestone_id: int,
    task_id: int,
    db: Session = Depends(get_db),
):
    task_service.delete_milestone_task(
        db=db,
        milestone_id=milestone_id,
        task_id=task_id,
    )
    return {
        "success": True,
        "message": "Task deleted successfully.",
    }
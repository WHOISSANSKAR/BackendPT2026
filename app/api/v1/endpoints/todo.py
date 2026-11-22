
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer
from app.models.project_owner import ProjectOwner
from app.schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoStatusUpdate,
    TodoResponse,
)
from app.services import todo_service


router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)


@router.get("/", response_model=list[TodoResponse])
def read_todos(
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    return todo_service.get_todos(db, current_customer)


@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_todo(
    todo_data: TodoCreate,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    return todo_service.create_todo(
        db, todo_data, current_customer
    )


@router.patch("/{td_id}", response_model=TodoResponse)
def edit_todo(
    td_id: int,
    todo_data: TodoUpdate,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    return todo_service.update_todo(
        db, td_id, todo_data, current_customer
    )


@router.patch(
    "/{td_id}/status",
    response_model=TodoResponse,
)
def change_todo_status(
    td_id: int,
    status_data: TodoStatusUpdate,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    return todo_service.update_todo_status(
        db,
        td_id,
        status_data.td_status,
        current_customer,
    )


@router.delete("/{td_id}")
def remove_todo(
    td_id: int,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    return todo_service.delete_todo(
        db, td_id, current_customer
    )

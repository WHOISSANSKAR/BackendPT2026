
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.todo import Todo
from app.models.project_owner import ProjectOwner
from app.schemas.todo import TodoCreate, TodoUpdate


def get_customer_todo(
    db: Session,
    td_id: int,
    customer: ProjectOwner,
):
    todo = db.scalar(
        select(Todo).where(
            Todo.td_id == td_id,
            Todo.td_user_id == customer.pown_id,
            Todo.td_user_type == "customer",
        )
    )

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found.",
        )

    return todo


def get_todos(
    db: Session,
    customer: ProjectOwner,
):
    return db.scalars(
        select(Todo)
        .where(
            Todo.td_user_id == customer.pown_id,
            Todo.td_user_type == "customer",
        )
        .order_by(Todo.td_date.asc(), Todo.td_id.desc())
    ).all()


def create_todo(
    db: Session,
    todo_data: TodoCreate,
    customer: ProjectOwner,
):
    if todo_data.td_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot create a Todo for a past date.",
        )

    todo = Todo(
        td_user_id=customer.pown_id,
        td_user_type="customer",
        td_event=todo_data.td_event.strip(),
        td_date=todo_data.td_date.isoformat(),
        td_status="pending",
    )

    db.add(todo)
    db.commit()
    db.refresh(todo)

    return todo


def update_todo(
    db: Session,
    td_id: int,
    todo_data: TodoUpdate,
    customer: ProjectOwner,
):
    todo = get_customer_todo(db, td_id, customer)

    if todo_data.td_date is not None:
        if todo_data.td_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot set a Todo to a past date.",
            )

        todo.td_date = todo_data.td_date.isoformat()

    if todo_data.td_event is not None:
        todo.td_event = todo_data.td_event.strip()

    db.commit()
    db.refresh(todo)

    return todo


def update_todo_status(
    db: Session,
    td_id: int,
    new_status: str,
    customer: ProjectOwner,
):
    todo = get_customer_todo(db, td_id, customer)

    try:
        todo_date = date.fromisoformat(todo.td_date)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Todo has an invalid date.",
        )

    if todo_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change the status of a past Todo.",
        )

    if new_status not in ("pending", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Todo status.",
        )

    todo.td_status = new_status

    db.commit()
    db.refresh(todo)

    return todo


def delete_todo(
    db: Session,
    td_id: int,
    customer: ProjectOwner,
):
    todo = get_customer_todo(db, td_id, customer)

    db.delete(todo)
    db.commit()

    return {"message": "Todo deleted successfully."}

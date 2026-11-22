
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    td_event: str = Field(..., min_length=1, max_length=255)
    td_date: date

    @field_validator("td_date")
    @classmethod
    def validate_todo_date(cls, value: date):
        if value < date.today():
            raise ValueError("You cannot create a Todo for a past date.")
        return value


class TodoUpdate(BaseModel):
    td_event: str | None = Field(default=None, min_length=1, max_length=255)
    td_date: date | None = None

    @field_validator("td_date")
    @classmethod
    def validate_todo_date(cls, value):
        if value is not None and value < date.today():
            raise ValueError("You cannot set a Todo to a past date.")
        return value


class TodoStatusUpdate(BaseModel):
    td_status: Literal["pending", "completed"]


class TodoResponse(BaseModel):
    td_id: int
    td_user_id: int
    td_user_type: str
    td_event: str
    td_date: date
    td_status: str

    model_config = {"from_attributes": True}

from typing import Literal
from pydantic import BaseModel


class TicketStatusUpdate(BaseModel):
    status: Literal[
        "Open",
        "In Progress",
        "Pending",
        "Resolved",
        "Closed",
    ]


class TicketCreateResponse(BaseModel):
    success: bool
    message: str
    ticket: dict
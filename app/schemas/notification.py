from pydantic import BaseModel
from typing import Optional


class NotificationItem(BaseModel):
    id: int
    title: str
    message: str
    link: Optional[str] = None
    projectId: str
    read: bool
    type: str
    time: str


class NotificationListResponse(BaseModel):
    success: bool
    notifications: list[NotificationItem]
    unread_count: int


class NotificationActionResponse(BaseModel):
    success: bool
    message: str
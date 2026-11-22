from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.schemas.notification import (
    NotificationListResponse,
    NotificationActionResponse
)

from app.services.notification_service import (
    get_customer_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read
)


router = APIRouter(
    prefix="/notifications",
    tags=["Customer Notifications"]
)


@router.get("", response_model=NotificationListResponse)
def customer_notifications(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer)
):
    customer_id = str(current_customer.pown_id)

    return get_customer_notifications(
        db=db,
        customer_id=customer_id
    )


@router.patch("/{notification_id}/read", response_model=NotificationActionResponse)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer)
):
    customer_id = str(current_customer.pown_id)

    return mark_notification_as_read(
        db=db,
        customer_id=customer_id,
        notification_id=notification_id
    )


@router.patch("/read-all", response_model=NotificationActionResponse)
def read_all_notifications(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer)
):
    customer_id = str(current_customer.pown_id)

    return mark_all_notifications_as_read(
        db=db,
        customer_id=customer_id
    )
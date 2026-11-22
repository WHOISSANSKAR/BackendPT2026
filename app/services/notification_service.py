from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException

from app.models.notification import Notification


def get_customer_notifications(db: Session, customer_id: str):

    notifications = (
        db.query(Notification)
        .filter(Notification.ntfn_forUserId == customer_id)
        .order_by(desc(Notification.ntfn_id))
        .all()
    )

    unread_count = (
        db.query(func.count(Notification.ntfn_id))
        .filter(
            Notification.ntfn_forUserId == customer_id,
            Notification.ntfn_readflag == False
        )
        .scalar()
    ) or 0

    result = []

    for notification in notifications:
        result.append({
            "id": notification.ntfn_id,
            "title": notification.ntfn_type,
            "message": notification.ntfn_notification,
            "link": notification.ntfn_hyperlink,
            "projectId": notification.ntfn_project_id,
            "read": notification.ntfn_readflag,
            "type": notification.ntfn_type,
            "time": notification.ntfn_date_time
        })

    return {
        "success": True,
        "notifications": result,
        "unread_count": unread_count
    }


def mark_notification_as_read(
    db: Session,
    customer_id: str,
    notification_id: int
):

    notification = (
        db.query(Notification)
        .filter(
            Notification.ntfn_id == notification_id,
            Notification.ntfn_forUserId == customer_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.ntfn_readflag = True

    db.commit()

    return {
        "success": True,
        "message": "Notification marked as read"
    }


def mark_all_notifications_as_read(db: Session, customer_id: str):

    db.query(Notification).filter(
        Notification.ntfn_forUserId == customer_id,
        Notification.ntfn_readflag == False
    ).update(
        {Notification.ntfn_readflag: True},
        synchronize_session=False
    )

    db.commit()

    return {
        "success": True,
        "message": "All notifications marked as read"
    }
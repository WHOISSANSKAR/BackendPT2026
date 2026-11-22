
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_owner import ProjectOwner
from app.models.project import Project
from app.models.notification import Notification
from app.models.cart import Cart
from app.models.todo import Todo


# =========================================================
# HELPER: GET PROJECT STATUS
# =========================================================

def get_project_status(project: Project) -> str:
    """
    Use plist_project_status as primary status.
    Fall back to plist_status if empty.
    """

    return re.sub(
        r"\s+",
        " ",
        (
            project.plist_project_status
            or project.plist_status
            or ""
        ).strip().lower(),
    )


def get_project_status_display(project: Project) -> str:
    """
    Return project status for frontend.
    """

    return (
        project.plist_project_status
        or project.plist_status
        or "Unknown"
    ).strip()


# =========================================================
# 1. PROJECT KPI COUNTS
# =========================================================

def calculate_project_kpis(
    projects: list[Project],
) -> dict[str, int]:

    not_started = 0
    in_progress = 0
    completed = 0
    critical = 0

    for project in projects:

        project_status = get_project_status(project)

        if project_status == "not started":
            not_started += 1

        elif project_status == "in progress":
            in_progress += 1

        elif project_status in ["completed", "delivered"]:
            completed += 1

        elif project_status in ["critical", "at risk", "on hold"]:
            critical += 1

    return {
        "totalProjects": len(projects),
        "notStarted": not_started,
        "inProgress": in_progress,
        "completed": completed,
        "critical": critical,
    }


# =========================================================
# 2. PROJECT PROGRESS GRAPH DATA
# =========================================================

def calculate_project_progress_data(
    projects: list[Project],
) -> list[dict[str, Any]]:

    # These are estimated percentages based on status.
    # Actual milestone/task progress should replace these
    # values when that data is connected.

    progress_map = {
        "delivered": 100,
        "completed": 100,
        "in progress": 50,
        "no sp assigned": 0,
        "not started": 0,
        "on hold": 0,
        "at risk": 0,
        "critical": 0,
    }

    progress_data = []

    for project in projects:

        project_status = get_project_status(project)

        progress = progress_map.get(project_status, 0)

        progress_data.append({
            "id": project.plist_id,
            "projectId": project.plist_projectid,
            "title": project.plist_title,
            "status": get_project_status_display(project),
            "progress": progress,
        })

    return progress_data


# =========================================================
# 3. OVERALL PROJECT PROGRESS
# =========================================================

def calculate_overall_project_progress(
    projects: list[Project],
) -> int:

    progress_map = {
        "delivered": 100,
        "completed": 100,
        "in progress": 50,
        "no sp assigned": 0,
        "not started": 0,
        "on hold": 0,
        "at risk": 0,
        "critical": 0,
    }

    if not projects:
        return 0

    total_progress = 0

    for project in projects:

        project_status = get_project_status(project)

        progress = progress_map.get(project_status, 0)

        total_progress += progress

    return round(total_progress / len(projects))


# =========================================================
# 4. SERIALIZE PROJECT
# =========================================================

def serialize_project(
    project: Project,
) -> dict[str, Any]:

    project_status = get_project_status_display(project)

    return {
        "id": project.plist_id,
        "projectId": project.plist_projectid,
        "title": project.plist_title,
        "description": project.plist_description,
        "type": project.plist_type,

        "country": project.plist_country,
        "state": project.plist_state,
        "city": project.plist_city,

        "startDate": project.plist_startdate,
        "endDate": project.plist_enddate,

        "currency": project.plist_currency,

        "budget": float(project.plist_budget or 0),

        "finalPrice": (
            float(project.plist_final_price)
            if project.plist_final_price is not None
            else None
        ),

        "customerName": project.plist_name,
        "customerEmail": project.plist_email,
        "customerContact": project.plist_contact,

        "status": project_status,
        "projectStatus": project_status,

        "deliveredOn": project.plist_delivered_on,
        "paymentOn": project.plist_payment_on,

        "category": project.plist_category,
        "statusDescription": project.plist_project_status_description,

        "createdAt": project.created_at,
        "updatedAt": project.updated_at,
    }


# =========================================================
# 5. SERIALIZE NOTIFICATION
# =========================================================

def serialize_notification(
    notification: Notification,
) -> dict[str, Any]:

    return {
        "id": notification.ntfn_id,
        "title": notification.ntfn_notification,
        "message": notification.ntfn_notification,
        "time": notification.ntfn_date_time,
        "read": bool(notification.ntfn_readflag),
        "link": notification.ntfn_hyperlink,
        "projectId": notification.ntfn_project_id,
        "type": notification.ntfn_type,
    }


# =========================================================
# 6. SERIALIZE CART ITEM
# =========================================================

def serialize_cart_item(
    item: Cart,
) -> dict[str, Any]:

    return {
        "id": item.cart_id,
        "spareId": item.cart_hw_id,
        "quantity": item.cart_qty,

        "unitPrice": (
            float(item.cart_hw_amt)
            if item.cart_hw_amt is not None
            else None
        ),

        "orderNumber": item.cart_order_no,
    }


# =========================================================
# 7. SERIALIZE CALENDAR EVENT
# =========================================================

def serialize_calendar_event(
    todo: Todo,
) -> dict[str, Any]:

    return {
        "id": todo.td_id,
        "title": todo.td_event,
        "date": todo.td_date,
        "userId": todo.td_user_id,
        "userType": todo.td_user_type,
    }


# =========================================================
# 8. CUSTOMER DASHBOARD SERVICE
# =========================================================

def get_customer_dashboard(
    db: Session,
    customer: ProjectOwner,
) -> dict[str, Any]:

    customer_id = str(customer.pown_id)

    # -----------------------------------------------------
    # A. FETCH ALL CUSTOMER PROJECTS
    # -----------------------------------------------------

    projects = db.scalars(
        select(Project)
        .where(
            Project.plist_customer_id == customer_id
        )
        .order_by(
            Project.plist_id.desc()
        )
    ).all()

    projects = list(projects)

    # -----------------------------------------------------
    # B. FETCH LATEST FIVE PROJECTS
    # EXCLUDE DELIVERED PROJECTS
    # -----------------------------------------------------

    recent_projects = [
        project
        for project in projects
        if get_project_status(project) != "delivered"
    ][:5]

    # -----------------------------------------------------
    # C. PROJECT KPI COUNTS
    # -----------------------------------------------------

    project_kpis = calculate_project_kpis(projects)

    # -----------------------------------------------------
    # D. PROJECT PROGRESS GRAPH DATA
    # -----------------------------------------------------

    project_progress = calculate_project_progress_data(
        projects
    )

    # -----------------------------------------------------
    # E. OVERALL PROJECT PROGRESS
    # -----------------------------------------------------

    overall_progress = calculate_overall_project_progress(
        projects
    )

    # -----------------------------------------------------
    # F. FETCH CUSTOMER NOTIFICATIONS
    # -----------------------------------------------------

    notifications = db.scalars(
        select(Notification)
        .where(
            Notification.ntfn_forUserId == customer_id,
            Notification.ntfn_type == "cust",
        )
        .order_by(
            Notification.ntfn_id.desc()
        )
    ).all()

    notifications = list(notifications)

    unread_notifications_count = sum(
        1
        for notification in notifications
        if not notification.ntfn_readflag
    )

    # -----------------------------------------------------
    # G. FETCH CUSTOMER CART ITEMS
    # -----------------------------------------------------

    cart_items = db.scalars(
        select(Cart)
        .where(
            Cart.cart_customer_id == customer_id
        )
        .order_by(
            Cart.cart_id.desc()
        )
    ).all()

    cart_items = list(cart_items)

    # -----------------------------------------------------
    # H. FETCH CUSTOMER CALENDAR EVENTS
    # -----------------------------------------------------

    calendar_events = db.scalars(
        select(Todo)
        .where(
            Todo.td_user_id == customer.pown_id,
            Todo.td_user_type == "customer",
        )
        .order_by(
            Todo.td_date.asc(),
            Todo.td_id.asc(),
        )
    ).all()

    calendar_events = list(calendar_events)

    # -----------------------------------------------------
    # I. FINAL DASHBOARD RESPONSE
    # -----------------------------------------------------

    return {
        "user": {
            "id": customer.pown_id,
            "name": customer.pown_name,
            "username": customer.pown_username,
            "email": customer.pown_email,
            "profile_complete": bool(
                customer.pown_profile_completion_flag
            ),
        },

        "dashboard": {

            # All customer projects
            "projects": [
                serialize_project(project)
                for project in projects
            ],

            # Latest five projects
            "recentProjects": [
                serialize_project(project)
                for project in recent_projects
            ],

            # Project KPIs
            "projectKpis": project_kpis,

            # Project progress graph
            "projectProgress": project_progress,

            # Overall progress
            "overallProgress": overall_progress,

            # Notifications
            "unreadNotificationsCount": unread_notifications_count,

            "notifications": [
                serialize_notification(notification)
                for notification in notifications
            ],

            # Cart
            "cartCount": len(cart_items),

            "addedToCart": [
                serialize_cart_item(item)
                for item in cart_items
            ],

            # Calendar
            "calendarEvents": [
                serialize_calendar_event(event)
                for event in calendar_events
            ],
        },
    }
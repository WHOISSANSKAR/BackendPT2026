
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from datetime import datetime


# ==================================================
# GET ALL CUSTOMER TICKETS
# ==================================================

def get_customer_tickets(db: Session, customer_id: str) -> dict:
    tickets = (
        db.query(Ticket)
        .filter(Ticket.tckt_customer_id == str(customer_id))
        .order_by(Ticket.tckt_id.desc())
        .all()
    )

    open_count = 0
    in_progress_count = 0
    resolved_count = 0

    ticket_list = []

    for ticket in tickets:
        status = (ticket.tckt_status or "Open").strip()
        normalized_status = status.lower()

        if normalized_status == "open":
            open_count += 1

        elif normalized_status in ("in progress", "pending"):
            in_progress_count += 1

        elif normalized_status == "resolved":
            resolved_count += 1

        date_time = ticket.tckt_date_time

        created_date = (
            date_time.strftime("%Y-%m-%d %H:%M:%S")
            if date_time
            else ticket.created_at
        )

        # Check whether an attachment exists without loading
        # the actual BLOB into the tickets-list response.
        attachment_exists = (
            db.query(Ticket.tckt_id)
            .filter(
                Ticket.tckt_id == ticket.tckt_id,
                Ticket.tckt_attachment.isnot(None),
            )
            .first()
            is not None
        )

        ticket_list.append({
            "id": ticket.tckt_id,
            "ticketNumber": f"TKT-{ticket.tckt_id:05d}",
            "title": ticket.tckt_title,
            "description": ticket.tckt_description,
            "project": ticket.tckt_project_id or "General",
            "projectId": ticket.tckt_project_id,
            "status": status,
            "createdDate": created_date or "",
            "dateTime": created_date,
            "conversationId": ticket.tckt_conversation_id,
            "assignedToPtId": ticket.tckt_asgnd_to_pt_id,
            "assignedToSpId": ticket.tckt_asgnd_to_sp_id,
            "attachmentAvailable": attachment_exists,
            "createdAt": ticket.created_at,
            "updatedAt": ticket.updated_at,
            "assignee": "",
        })

    return {
        "success": True,
        "message": "Customer tickets fetched successfully",
        "counts": {
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "total": len(tickets),
        },
        "total_tickets": len(tickets),
        "tickets": ticket_list,
    }


# ==================================================
# GET SINGLE CUSTOMER TICKET DETAILS
# ==================================================

def get_customer_ticket_detail(
    db: Session,
    ticket_id: int,
    customer_id: str,
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.tckt_id == ticket_id,
            Ticket.tckt_customer_id == str(customer_id),
        )
        .first()
    )

    if not ticket:
        return None

    attachment_exists = (
        db.query(Ticket.tckt_id)
        .filter(
            Ticket.tckt_id == ticket_id,
            Ticket.tckt_customer_id == str(customer_id),
            Ticket.tckt_attachment.isnot(None),
        )
        .first()
        is not None
    )

    date_time = ticket.tckt_date_time

    created_date = (
        date_time.strftime("%Y-%m-%d %H:%M:%S")
        if date_time
        else ticket.created_at
    )

    return {
        "id": ticket.tckt_id,
        "ticketNumber": f"TKT-{ticket.tckt_id:05d}",
        "title": ticket.tckt_title,
        "description": ticket.tckt_description,
        "project": ticket.tckt_project_id or "General",
        "projectId": ticket.tckt_project_id,
        "status": ticket.tckt_status or "Open",
        "createdDate": created_date or "",
        "dateTime": created_date,
        "conversationId": ticket.tckt_conversation_id,
        "assignedToPtId": ticket.tckt_asgnd_to_pt_id,
        "assignedToSpId": ticket.tckt_asgnd_to_sp_id,
        "attachmentAvailable": attachment_exists,
        "createdAt": ticket.created_at,
        "updatedAt": ticket.updated_at,
        "assignee": "",
    }


# ==================================================
# UPDATE CUSTOMER TICKET STATUS
# ==================================================

def update_customer_ticket_status(
    db: Session,
    ticket_id: int,
    customer_id: str,
    new_status: str,
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.tckt_id == ticket_id,
            Ticket.tckt_customer_id == str(customer_id),
        )
        .first()
    )

    if not ticket:
        return None

    try:
        ticket.tckt_status = new_status
        db.commit()
        db.refresh(ticket)

        return {
            "id": ticket.tckt_id,
            "ticketNumber": f"TKT-{ticket.tckt_id:05d}",
            "status": ticket.tckt_status,
            "message": "Ticket status updated successfully",
        }

    except Exception:
        db.rollback()
        raise


# ==================================================
# GET CUSTOMER TICKET ATTACHMENT
# ==================================================

def get_customer_ticket_attachment(
    db: Session,
    ticket_id: int,
    customer_id: str,
):
    # Select only the attachment column.
    # This avoids loading the other ticket fields unnecessarily.
    attachment = (
        db.query(Ticket.tckt_attachment)
        .filter(
            Ticket.tckt_id == ticket_id,
            Ticket.tckt_customer_id == str(customer_id),
        )
        .scalar()
    )

    return attachment


def create_customer_ticket(
    db: Session,
    customer_id: str,
    project_id: str,
    title: str,
    description: str = "",
    attachment: bytes | None = None,
):
    now = datetime.now()
    formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

    ticket = Ticket(
        tckt_project_id=str(project_id),
        tckt_title=title.strip(),
        tckt_description=description.strip(),
        tckt_date_time=now,
        tckt_status="Open",
        tckt_customer_id=str(customer_id),
        tckt_attachment=attachment,
        created_at=formatted_now,
        updated_at=formatted_now,
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return {
            "id": ticket.tckt_id,
            "ticketNumber": f"TKT-{ticket.tckt_id:05d}",
            "title": ticket.tckt_title,
            "description": ticket.tckt_description,
            "project": ticket.tckt_project_id or "General",
            "projectId": ticket.tckt_project_id,
            "status": ticket.tckt_status,
            "createdDate": formatted_now,
            "dateTime": formatted_now,
            "conversationId": ticket.tckt_conversation_id,
            "assignedToPtId": ticket.tckt_asgnd_to_pt_id,
            "assignedToSpId": ticket.tckt_asgnd_to_sp_id,
            "attachmentAvailable": attachment is not None,
            "createdAt": ticket.created_at,
            "updatedAt": ticket.updated_at,
            "assignee": "",
        }

    except Exception:
        db.rollback()
        raise
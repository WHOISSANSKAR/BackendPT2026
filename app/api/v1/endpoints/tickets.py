
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Form,
    File,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.schemas.ticket import TicketStatusUpdate

from app.services.ticket_service import (
    get_customer_tickets,
    get_customer_ticket_detail,
    update_customer_ticket_status,
    get_customer_ticket_attachment,
    create_customer_ticket,
)


router = APIRouter()


# ==================================================
# CREATE CUSTOMER TICKET
# POST /api/v1/customer/tickets/
# ==================================================

@router.post("/")
async def create_ticket(
    project_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    attachment: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    attachment_data = None

    if attachment is not None:
        attachment_data = await attachment.read()

        if not attachment_data:
            attachment_data = None

    result = create_customer_ticket(
        db=db,
        customer_id=customer_id,
        project_id=project_id,
        title=title,
        description=description,
        attachment=attachment_data,
    )

    return {
        "success": True,
        "message": "Ticket created successfully",
        "ticket": result,
    }


# ==================================================
# GET ALL CUSTOMER TICKETS
# GET /api/v1/customer/tickets/
# ==================================================

@router.get("/")
def fetch_customer_tickets(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    return get_customer_tickets(
        db=db,
        customer_id=customer_id,
    )


# ==================================================
# GET SINGLE TICKET DETAILS
# GET /api/v1/customer/tickets/{ticket_id}
# ==================================================

@router.get("/{ticket_id}")
def fetch_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    ticket = get_customer_ticket_detail(
        db=db,
        ticket_id=ticket_id,
        customer_id=customer_id,
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return {
        "success": True,
        "message": "Ticket details fetched successfully",
        "ticket": ticket,
    }


# ==================================================
# UPDATE TICKET STATUS
# PATCH /api/v1/customer/tickets/{ticket_id}/status
# ==================================================

@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    result = update_customer_ticket_status(
        db=db,
        ticket_id=ticket_id,
        customer_id=customer_id,
        new_status=payload.status,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return {
        "success": True,
        **result,
    }


# ==================================================
# DOWNLOAD TICKET ATTACHMENT
# GET /api/v1/customer/tickets/{ticket_id}/attachment
# ==================================================

@router.get("/{ticket_id}/attachment")
def download_ticket_attachment(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    attachment = get_customer_ticket_attachment(
        db=db,
        ticket_id=ticket_id,
        customer_id=customer_id,
    )

    if attachment is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket or attachment not found",
        )

    return Response(
        content=attachment,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f'attachment; filename="ticket-{ticket_id}-attachment"'
            )
        },
    )
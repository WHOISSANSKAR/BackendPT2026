
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.services.order_service import (
    get_customer_orders,
    get_customer_order_detail,
)


router = APIRouter()


# ==================================================
# GET ALL CUSTOMER ORDERS
# GET /api/v1/customer/orders/
# ==================================================

@router.get("/")
def fetch_customer_orders(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    return get_customer_orders(
        db=db,
        customer_id=customer_id,
    )


# ==================================================
# GET SINGLE ORDER DETAILS
# GET /api/v1/customer/orders/{order_id}
# ==================================================

@router.get("/{order_id}")
def fetch_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    customer_id = str(current_customer.pown_id)

    order = get_customer_order_detail(
        db=db,
        order_id=order_id,
        customer_id=customer_id,
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return {
        "success": True,
        "message": "Order details fetched successfully",
        "order": order,
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

# Replace with your actual DB session and current_customer auth dependencies
from database import get_db
from auth import get_current_customer

router = APIRouter(prefix="/api/v1/customer", tags=["Customer Orders"])


@router.get("/orders")
def get_customer_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_customer),
):
    customer_id = str(current_user.id)

    query = text("""
        SELECT
            o.ordplcd_id,
            o.ordplcd_hw_id,
            o.ordplcd_customer_id,
            o.ordplcd_address,
            o.ordplcd_qty_placed,
            o.ordplcd_no_of_items,
            o.ordplcd_order_no,
            o.ordplcd_amt,
            o.ordplcd_status,
            o.ordplcd_delivery_date,
            o.ordplcd_order_date,
            o.ordplcd_sp_id,
            o.ordplcd_final_qty,
            o.ordplcd_final_amount,
            o.created_at,
            o.updated_at
        FROM orders_placed o
        WHERE o.ordplcd_customer_id = :customer_id
        ORDER BY o.ordplcd_id DESC
    """)

    rows = db.execute(query, {"customer_id": customer_id}).mappings().all()

    orders = []
    for r in rows:
        orders.append({
            "ordplcd_id": r["ordplcd_id"],
            "ordplcd_hw_id": r["ordplcd_hw_id"],
            "ordplcd_customer_id": r["ordplcd_customer_id"],
            "ordplcd_address": r["ordplcd_address"],
            "ordplcd_qty_placed": int(r["ordplcd_qty_placed"] or 0),
            "ordplcd_no_of_items": int(r["ordplcd_no_of_items"] or 0),
            "ordplcd_order_no": r["ordplcd_order_no"],
            "ordplcd_amt": float(r["ordplcd_amt"] or 0),
            "ordplcd_status": r["ordplcd_status"] or "Pending",
            "ordplcd_delivery_date": r["ordplcd_delivery_date"],
            "ordplcd_order_date": r["ordplcd_order_date"],
            "ordplcd_sp_id": r["ordplcd_sp_id"],
            "ordplcd_final_qty": (
                int(r["ordplcd_final_qty"])
                if r["ordplcd_final_qty"] is not None
                else None
            ),
            "ordplcd_final_amount": (
                float(r["ordplcd_final_amount"])
                if r["ordplcd_final_amount"] is not None
                else None
            ),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })

    return {
        "success": True,
        "message": "Orders fetched successfully",
        "total_orders": len(orders),
        "orders": orders,
    }
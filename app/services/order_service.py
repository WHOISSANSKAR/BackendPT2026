
from sqlalchemy.orm import Session
from sqlalchemy import cast, String

from app.models.order_placed import OrderPlaced
from app.models.hardware import Hardware


def _serialize_order(order: OrderPlaced, hardware: Hardware | None) -> dict:
    # Supplier information available in the hardwares table.
    vendor = "Supplier"

    if hardware:
        vendor = (
            hardware.hrdws_sp_email
            or hardware.hrdws_sp_id
            or "Supplier"
        )
    elif order.ordplcd_sp_id:
        vendor = order.ordplcd_sp_id

    items_detail = []

    if hardware:
        item_name = hardware.hrdws_model_description or hardware.hrdws_model_number

        if item_name:
            items_detail.append(item_name)

    return {
        "id": str(order.ordplcd_id),
        "orderNumber": order.ordplcd_order_no,
        "vendor": vendor,

        "itemsCount": order.ordplcd_no_of_items,
        "itemsDetail": items_detail,

        "status": order.ordplcd_status,
        "date": order.ordplcd_order_date or "",

        "hardwareId": order.ordplcd_hw_id,
        "serialNo": hardware.hrdws_serial_number if hardware else None,
        "hwIdentifier": hardware.hrdws_hw_identifier if hardware else None,
        "modelNo": hardware.hrdws_model_number if hardware else None,
        "itemDescription": (
            hardware.hrdws_model_description if hardware else None
        ),
        "family": hardware.hrdws_family if hardware else None,

        "quantityPlaced": order.ordplcd_qty_placed,
        "finalQuantity": order.ordplcd_final_qty,

        "amount": float(order.ordplcd_amt),
        "finalAmount": (
            float(order.ordplcd_final_amount)
            if order.ordplcd_final_amount is not None
            else None
        ),

        "address": order.ordplcd_address,
        "deliveryDate": order.ordplcd_delivery_date,

        "supplierId": order.ordplcd_sp_id,
        "supplierEmail": hardware.hrdws_sp_email if hardware else None,

        "createdAt": order.created_at,
        "updatedAt": order.updated_at,
    }


# ==================================================
# GET ALL CUSTOMER ORDERS
# ==================================================

def get_customer_orders(
    db: Session,
    customer_id: str,
) -> dict:

    results = (
        db.query(OrderPlaced, Hardware)
       .outerjoin(
    Hardware,
    cast(Hardware.hrdws_id, String).collate("utf8mb4_general_ci")
    == OrderPlaced.ordplcd_hw_id.collate("utf8mb4_general_ci")
)
        .filter(
            OrderPlaced.ordplcd_customer_id == str(customer_id)
        )
        .order_by(OrderPlaced.ordplcd_id.desc())
        .all()
    )

    orders = []

    for order, hardware in results:
        orders.append(
            _serialize_order(order, hardware)
        )

    return {
        "success": True,
        "message": "Customer orders fetched successfully",
        "total_orders": len(orders),
        "orders": orders,
    }


# ==================================================
# GET SINGLE CUSTOMER ORDER DETAILS
# ==================================================

def get_customer_order_detail(
    db: Session,
    order_id: int,
    customer_id: str,
):

    result = (
        db.query(OrderPlaced, Hardware)
        .outerjoin(
            Hardware,
            cast(Hardware.hrdws_id, String) == OrderPlaced.ordplcd_hw_id,
        )
        .filter(
            OrderPlaced.ordplcd_id == order_id,
            OrderPlaced.ordplcd_customer_id == str(customer_id),
        )
        .first()
    )

    if not result:
        return None

    order, hardware = result

    return _serialize_order(order, hardware)

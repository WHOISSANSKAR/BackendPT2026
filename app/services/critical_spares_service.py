
from sqlalchemy.orm import Session

from app.models.hardware import Hardware


def get_critical_spares(db: Session) -> dict:
    hardware_items = (
        db.query(Hardware)
        .order_by(Hardware.hrdws_id.desc())
        .all()
    )

    spares = []

    for item in hardware_items:
        spare = {
            "id": item.hrdws_id,
            "serialNo": item.hrdws_serial_number,
            "hwIdentifier": item.hrdws_hw_identifier,
            "modelNo": item.hrdws_model_number,
            "name": item.hrdws_model_description,
            "qty": item.hrdws_qty,
            "stock": item.hrdws_qty,
            "family": item.hrdws_family,
            "category": item.hrdws_family,
            "city": item.hrdws_city,
            "state": item.hrdws_state,
            "price": float(item.hrdws_price),
            "spEmail": item.hrdws_sp_email,
            "spId": item.hrdws_sp_id,
            "status": item.hrdws_hw_status,
            "createdAt": item.created_at,
            "updatedAt": item.updated_at,
        }

        spares.append(spare)

    return {
        "success": True,
        "message": "Critical spares fetched successfully",
        "total_spares": len(spares),
        "spares": spares,
    }

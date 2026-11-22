# changes done by vb
import re
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.hardware import Hardware
from app.models.order_address import OrderAddress
from app.models.order_placed import OrderPlaced
from app.services.order_service import _serialize_order


def _now_ist() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def _address_out(row: OrderAddress) -> dict:
    return {"id": row.ordradrs_id, "address": row.ordradrs_address, "created_at": row.created_at}


def list_addresses(db: Session, owner_id: int) -> dict:
    rows = (
        db.query(OrderAddress)
        .filter(OrderAddress.ordradrs_projectowner_id == owner_id)
        .order_by(OrderAddress.ordradrs_id.desc())
        .all()
    )
    return {"success": True, "addresses": [_address_out(r) for r in rows]}


def add_address(db: Session, owner_id: int, address: str) -> dict:
    text = " ".join(address.split())
    if len(text) < 5:
        raise HTTPException(status_code=422, detail="Please enter a complete address.")

    existing = (
        db.query(OrderAddress)
        .filter(
            OrderAddress.ordradrs_projectowner_id == owner_id,
            OrderAddress.ordradrs_address == text,
        )
        .first()
    )
    if existing:
        return {"success": True, "message": "Address already saved", "address": _address_out(existing)}

    ts = _now_ist().strftime("%Y-%m-%d %H:%M:%S")
    row = OrderAddress(ordradrs_projectowner_id=owner_id, ordradrs_address=text, created_at=ts, updated_at=ts)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "message": "Address saved", "address": _address_out(row)}


def _next_order_seq(db: Session, year: int) -> int:
    prefix = f"ORD-{year}-"
    pattern = re.compile(re.escape(prefix) + r"(\d+)")
    nums = []
    for (no,) in db.query(OrderPlaced.ordplcd_order_no).filter(OrderPlaced.ordplcd_order_no.like(prefix + "%")).all():
        m = pattern.fullmatch(no or "")
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1001


def place_order(db: Session, owner_id: int, address_id: int, items: list) -> dict:
    address = (
        db.query(OrderAddress)
        .filter(OrderAddress.ordradrs_id == address_id, OrderAddress.ordradrs_projectowner_id == owner_id)
        .first()
    )
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found.")

    qty_by_hw: dict[int, int] = {}
    for item in items:
        qty_by_hw[item.hardware_id] = qty_by_hw.get(item.hardware_id, 0) + item.quantity

    hardware = {
        h.hrdws_id: h
        for h in db.query(Hardware).filter(Hardware.hrdws_id.in_(list(qty_by_hw.keys()))).all()
    }
    for hw_id, qty in qty_by_hw.items():
        hw = hardware.get(hw_id)
        if not hw:
            raise HTTPException(status_code=404, detail=f"Spare part {hw_id} not found.")
        if qty > (hw.hrdws_qty or 0):
            raise HTTPException(
                status_code=409,
                detail=f"Only {hw.hrdws_qty} unit(s) of {hw.hrdws_model_number} available.",
            )

    now = _now_ist()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    seq = _next_order_seq(db, now.year)
    created: list[tuple[OrderPlaced, Hardware]] = []

    try:
        for hw_id, qty in qty_by_hw.items():
            hw = hardware[hw_id]
            order = OrderPlaced(
                ordplcd_hw_id=str(hw_id),
                ordplcd_customer_id=str(owner_id),
                ordplcd_address=address.ordradrs_address,
                ordplcd_qty_placed=qty,
                ordplcd_no_of_items=1,
                ordplcd_order_no=f"ORD-{now.year}-{seq}",
                ordplcd_amt=Decimal(str(hw.hrdws_price)) * qty,
                ordplcd_status="Pending",
                ordplcd_order_date=now.strftime("%Y-%m-%d"),
                ordplcd_sp_id=hw.hrdws_sp_id,
                created_at=ts,
                updated_at=ts,
            )
            db.add(order)
            created.append((order, hw))
            seq += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    for order, _ in created:
        db.refresh(order)

    return {
        "success": True,
        "message": f"{len(created)} order(s) placed",
        "orders": [_serialize_order(o, hw) for o, hw in created],
    }

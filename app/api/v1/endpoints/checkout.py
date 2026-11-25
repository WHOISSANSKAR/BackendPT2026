# changes done by vb
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_customer
from app.db.database import get_db
from app.schemas.checkout import AddressCreate, PlaceOrderRequest
from app.services.checkout_service import add_address, list_addresses, place_order

router = APIRouter()


@router.get("/order-addresses")
def fetch_addresses(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return list_addresses(db, int(current_customer.pown_id))


@router.post("/order-addresses", status_code=201)
def create_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return add_address(db, int(current_customer.pown_id), payload.address)


@router.post("/orders/place", status_code=201)
def create_order(
    payload: PlaceOrderRequest,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return place_order(
        db,
        int(current_customer.pown_id),
        payload.address_id,
        payload.items,
    )

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer
from app.services.critical_spares_service import get_critical_spares


router = APIRouter()


@router.get("/")
def fetch_critical_spares(
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return get_critical_spares(db)

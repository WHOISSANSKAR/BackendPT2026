
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer
from app.models.project_owner import ProjectOwner
from app.services.dashboard_service import get_customer_dashboard

router = APIRouter()


@router.get("/dashboard")
def customer_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(get_current_customer),
):
    result = get_customer_dashboard(
        db=db,
        customer=current_customer,
    )

    return {
        "success": True,
        "message": "Dashboard data fetched successfully",
        **result,
    }

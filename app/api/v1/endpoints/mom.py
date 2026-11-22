# changes done by vb: Minutes of Meeting (MOM) endpoint for the customer portal (read-only).
#   GET /api/v1/customer/projects/{project_id}/moms
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_customer
from app.db.database import get_db
from app.schemas.mom import ProjectMomsResponse
from app.services.mom_service import get_project_moms

router = APIRouter()


@router.get(
    "/projects/{project_id}/moms",
    response_model=ProjectMomsResponse,
)
def list_project_moms(
    project_id: int,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    return get_project_moms(
        db=db,
        customer_id=str(current_customer.pown_id),
        project_id=project_id,
    )

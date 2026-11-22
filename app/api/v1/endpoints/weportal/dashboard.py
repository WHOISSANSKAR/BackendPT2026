# app/api/v1/endpoints/weportal/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.weuser import WeUser
from app.schemas.weportal.dashboard import WePortalDashboardResponse
from app.services.weportal.dashboard_service import get_weportal_dashboard_data

router = APIRouter()


@router.get("", response_model=WePortalDashboardResponse)
def weportal_dashboard(
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    return get_weportal_dashboard_data(db=db, current_user=current_user)
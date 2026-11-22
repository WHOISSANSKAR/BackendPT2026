from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.weuser import WeUser
from app.schemas.weportal.my_projects import MyProjectsResponse
from app.services.weportal.my_projects_service import get_my_projects

router = APIRouter()


@router.get("", response_model=MyProjectsResponse)
def list_my_projects(
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    return get_my_projects(
        db=db,
        current_user=current_user,
        search=search,
        status=status,
    )
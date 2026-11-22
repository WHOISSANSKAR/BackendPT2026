from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.weuser import WeUser
from app.schemas.weportal.my_projects import WePortalMyProjectsResponse
from app.services.weportal.my_projects_service import get_weportal_my_projects

router = APIRouter()


@router.get("", response_model=WePortalMyProjectsResponse)
def weportal_my_projects(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> WePortalMyProjectsResponse:
    return get_weportal_my_projects(
        db=db,
        current_user=current_user,
        search=search,
        status=status,
    )
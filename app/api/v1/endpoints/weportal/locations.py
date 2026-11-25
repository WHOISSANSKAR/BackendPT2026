from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.weuser import WeUser
from app.schemas.weportal.locations import (
    LocationImportResponse,
    LocationWeightageSummaryResponse,
    ProjectLocationCreate,
    ProjectLocationListResponse,
    ProjectLocationOut,
    ProjectLocationUpdate,
)
from app.services.weportal.locations_service import (
    create_project_location,
    delete_project_location,
    get_location_weightage_sum,
    get_project_location,
    import_project_locations_excel,
    list_project_locations,
    update_project_location,
)

router = APIRouter()


@router.get("/{project_id}/locations", response_model=ProjectLocationListResponse)
def get_locations(
    project_id: int,
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> ProjectLocationListResponse:
    return list_project_locations(db=db, project_id=project_id, search=search)


@router.get(
    "/{project_id}/locations/weightage-sum",
    response_model=LocationWeightageSummaryResponse,
)
def get_weightage_sum(
    project_id: int,
    pscope_id: int | None = Query(default=None),
    entered_weightage: float | None = Query(default=None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> LocationWeightageSummaryResponse:
    return get_location_weightage_sum(
        db=db,
        project_id=project_id,
        exclude_pscope_id=pscope_id,
        entered_weightage=entered_weightage,
    )


@router.get(
    "/{project_id}/locations/{location_id}",
    response_model=ProjectLocationOut,
)
def get_location_detail(
    project_id: int,
    location_id: int,
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> ProjectLocationOut:
    return get_project_location(
        db=db, project_id=project_id, location_id=location_id
    )


@router.post(
    "/{project_id}/locations",
    response_model=ProjectLocationOut,
    status_code=status.HTTP_201_CREATED,
)
def add_location(
    project_id: int,
    payload: ProjectLocationCreate,
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> ProjectLocationOut:
    return create_project_location(
        db=db, project_id=project_id, payload=payload
    )


@router.patch(
    "/{project_id}/locations/{location_id}",
    response_model=ProjectLocationOut,
)
def edit_location(
    project_id: int,
    location_id: int,
    payload: ProjectLocationUpdate,
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> ProjectLocationOut:
    return update_project_location(
        db=db, project_id=project_id, location_id=location_id, payload=payload
    )


@router.delete(
    "/{project_id}/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_location(
    project_id: int,
    location_id: int,
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> None:
    delete_project_location(
        db=db, project_id=project_id, location_id=location_id
    )


@router.post(
    "/{project_id}/locations/import",
    response_model=LocationImportResponse,
)
async def import_locations(
    project_id: int,
    excel_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
) -> LocationImportResponse:
    if not excel_file.filename or not excel_file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid Excel file (.xlsx or .xls).",
        )
    content = await excel_file.read()
    return import_project_locations_excel(
        db=db, project_id=project_id, file_bytes=content
    )
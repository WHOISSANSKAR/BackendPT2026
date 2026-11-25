from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.weportal.milestones import (
    MilestoneCreate,
    MilestoneImportResponse,
    MilestoneItem,
    MilestoneListResponse,
    MilestoneUpdate,
    MilestoneWeightageSumResponse,
)
from app.services.weportal import milestones_service

router = APIRouter(
    prefix="/projects/{project_id}/locations/{location_id}/milestones",
    tags=["WePortal - Milestones"],
)


@router.get("", response_model=MilestoneListResponse)
def get_milestones(
    project_id: int,
    location_id: int,
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    total, milestones = milestones_service.list_milestones(
        db=db, project_id=project_id, location_id=location_id, search=search
    )
    return MilestoneListResponse(success=True, total=total, milestones=milestones)


@router.get("/weightage-sum", response_model=MilestoneWeightageSumResponse)
def fetch_milestone_weightage_sum(
    project_id: int,
    location_id: int,
    pplnr_id: Optional[int] = Query(default=None),
    entered_weightage: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    data = milestones_service.get_weightage_sum(
        db=db,
        project_id=project_id,
        location_id=location_id,
        exclude_milestone_id=pplnr_id,
        entered_weightage=entered_weightage,
    )
    return MilestoneWeightageSumResponse(**data)


@router.post("", response_model=MilestoneItem, status_code=status.HTTP_201_CREATED)
def add_milestone(
    project_id: int,
    location_id: int,
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
):
    return milestones_service.create_milestone(
        db=db, project_id=project_id, location_id=location_id, payload=payload
    )


@router.get("/{milestone_id}", response_model=MilestoneItem)
def read_milestone(
    project_id: int,
    location_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
):
    return milestones_service.get_milestone_by_id(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
    )


@router.patch("/{milestone_id}", response_model=MilestoneItem)
def edit_milestone(
    project_id: int,
    location_id: int,
    milestone_id: int,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
):
    return milestones_service.update_milestone(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        payload=payload,
    )


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_milestone(
    project_id: int,
    location_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
):
    milestones_service.delete_milestone(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
    )
    return None


@router.post("/import", response_model=MilestoneImportResponse)
def import_milestones(
    project_id: int,
    location_id: int,
    excel_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    count, created = milestones_service.import_milestones_from_excel(
        db=db, project_id=project_id, location_id=location_id, file=excel_file
    )
    return MilestoneImportResponse(
        success=True,
        message=f"Successfully imported {count} milestones.",
        imported_count=count,
        milestones=created,
    )
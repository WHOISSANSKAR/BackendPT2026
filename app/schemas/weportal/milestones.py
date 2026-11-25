from typing import Any, List, Optional
from pydantic import BaseModel


class MilestoneItem(BaseModel):
    id: str
    pplnr_id: Optional[int] = None
    title: Optional[str] = None
    pplnr_milestone: Optional[str] = None
    description: Optional[str] = None
    pplnr_description: Optional[str] = None
    status: Optional[str] = None
    pplnr_status: Optional[str] = None
    startDate: Optional[str] = None
    start_date: Optional[str] = None
    endDate: Optional[str] = None
    end_date: Optional[str] = None
    dueDate: Optional[str] = None
    due_date: Optional[str] = None
    addWeightage: bool = False
    add_weightage: bool = False
    weightage: Optional[float] = None
    pplnr_weightage: Optional[float] = None
    createdOn: Optional[str] = None
    created_on: Optional[str] = None
    assignedTo: Optional[str] = None
    tasks: List[Any] = []


class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    add_weightage: bool = False
    weightage: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = "Not Started"


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    add_weightage: Optional[bool] = None
    weightage: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None


MilestoneCreateRequest = MilestoneCreate
MilestoneUpdateRequest = MilestoneUpdate


class MilestoneWeightageSumResponse(BaseModel):
    success: bool = True
    total_weightage: float = 0.0
    remaining_weightage: float = 100.0
    entered_weightage: Optional[float] = None
    projected_total_weightage: Optional[float] = None
    remaining_after_add: Optional[float] = None
    exceeds_limit: bool = False


class MilestoneListResponse(BaseModel):
    success: bool = True
    total: int = 0
    milestones: List[MilestoneItem] = []


class MilestoneImportResponse(BaseModel):
    success: bool = True
    message: str = ""
    imported_count: int = 0
    milestones: List[MilestoneItem] = []
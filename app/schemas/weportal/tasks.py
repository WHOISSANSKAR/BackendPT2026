from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MilestoneTaskCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    title: str
    description: Optional[str] = ""
    add_weightage: Optional[bool] = Field(default=False, alias="addWeightage")
    weightage: Optional[float] = 0.0
    start_date: Optional[str] = Field(default=None, alias="startDate")
    end_date: Optional[str] = Field(default=None, alias="endDate")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    date_of_completion: Optional[str] = Field(
        default=None, alias="dateOfCompletion"
    )
    sp_id: Optional[str] = Field(default=None, alias="spId")
    sp_status: Optional[str] = Field(default="Not Started", alias="spStatus")
    status: Optional[str] = "Not Started"
    priority: Optional[str] = "Medium"
    payment: Optional[float] = 0.0


class MilestoneTaskUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    add_weightage: Optional[bool] = Field(default=None, alias="addWeightage")
    weightage: Optional[float] = None
    start_date: Optional[str] = Field(default=None, alias="startDate")
    end_date: Optional[str] = Field(default=None, alias="endDate")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    date_of_completion: Optional[str] = Field(
        default=None, alias="dateOfCompletion"
    )
    sp_id: Optional[str] = Field(default=None, alias="spId")
    sp_status: Optional[str] = Field(default=None, alias="spStatus")
    status: Optional[str] = None
    priority: Optional[str] = None
    payment: Optional[float] = None
    proof_completion_approved: Optional[int] = Field(
        default=None, alias="proofCompletionApproved"
    )
    invoice_raised_flag: Optional[int] = Field(
        default=None, alias="invoiceRaisedFlag"
    )
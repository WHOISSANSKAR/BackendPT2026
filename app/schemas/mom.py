# changes done by vb: response schemas for GET /api/v1/customer/projects/{project_id}/moms
# Field names match what the frontend's src/services/mom.service.ts reads.
from pydantic import BaseModel


class MomActionItemOut(BaseModel):
    id: int
    action: str
    owner: str | None = None
    due_date: str | None = None
    status: str


class MomOut(BaseModel):
    id: int
    project_id: int
    location_id: int | None = None
    location: str | None = None
    phase: str | None = None
    milestone: str | None = None
    task: str | None = None
    prepared_by: str
    prepared_on: str
    meeting_type: str | None = None
    attendees_present: list[str] = []
    attendees_absent: list[str] = []
    agenda: list[str] = []
    summary: str | None = None
    action_items: list[MomActionItemOut] = []
    next_meeting: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProjectMomsResponse(BaseModel):
    success: bool
    message: str
    project_id: int
    total: int
    moms: list[MomOut]

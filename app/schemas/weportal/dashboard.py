# app/schemas/weportal/dashboard.py
from pydantic import BaseModel


class WePortalDashboardCounts(BaseModel):
    project_owners: int
    service_providers: int
    project_list: int
    project_list_by_admin: int
    hardwares: int
    orders_pending: int
    orders_placed: int
    tickets_count: int


class WePortalRecentProject(BaseModel):
    plist_id: int
    plist_customer_id: int | None = None
    plist_projectid: str | None = None
    plist_title: str | None = None
    plist_description: str | None = None
    plist_startdate: str | None = None
    plist_enddate: str | None = None
    plist_status: str | None = None


class WePortalDashboardResponse(BaseModel):
    success: bool
    counts: WePortalDashboardCounts
    recent_projects: list[WePortalRecentProject]
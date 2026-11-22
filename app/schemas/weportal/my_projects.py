from pydantic import BaseModel


class WePortalMyProjectItem(BaseModel):
    plist_id: int
    plist_customer_id: int | None = None
    pown_id: int | None = None
    pown_name: str | None = None
    pown_username: str | None = None
    pown_user_type: str | None = None
    pown_organisation_name: str | None = None
    plist_projectid: str | None = None
    plist_title: str | None = None
    plist_description: str | None = None
    plist_startdate: str | None = None
    plist_enddate: str | None = None
    plist_status: str | None = None


class WePortalMyProjectsResponse(BaseModel):
    success: bool
    total: int
    projects: list[WePortalMyProjectItem]

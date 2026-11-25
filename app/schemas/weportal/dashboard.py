from pydantic import BaseModel


class WePortalDashboardCounts(BaseModel):
    project_owners: int = 0
    service_providers: int = 0
    project_list: int = 0
    project_list_by_admin: int = 0
    hardwares: int = 0
    orders_pending: int = 0
    orders_placed: int = 0
    tickets_count: int = 0
    unread_notifications_count: int = 0
    hardware_orders_count: int = 0


class WePortalRecentProject(BaseModel):
    plist_id: int
    plist_customer_id: int | None = None
    customer_name: str | None = None
    plist_projectid: str | None = None
    plist_title: str | None = None
    plist_description: str | None = None
    plist_startdate: str | None = None
    plist_enddate: str | None = None
    plist_status: str | None = None


class WePortalNotificationItem(BaseModel):
    ntfn_id: int
    ntfn_notification: str
    ntfn_hyperlink: str | None = None
    ntfn_readflag: bool
    ntfn_project_id: str | None = None
    ntfn_date_time: str | None = None
    ntfn_type: str | None = None


class WePortalDashboardResponse(BaseModel):
    success: bool
    counts: WePortalDashboardCounts
    recent_projects: list[WePortalRecentProject]
    notifications: list[WePortalNotificationItem] = []
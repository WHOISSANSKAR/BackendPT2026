from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.weportal.auth import router as weportal_auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.project import router as projects
from app.api.v1.endpoints.project_tracking import router as project_tracking
from app.api.v1.endpoints.critical_spares import router as critical_spares
from app.api.v1.endpoints.tickets import router as tickets
from app.api.v1.endpoints.orders import router as orders
from app.api.v1.endpoints.checkout import router as checkout_router
from app.api.v1.endpoints.account import router as account
from app.api.v1.endpoints.comments import router as comments
from app.api.v1.endpoints import notifications
from app.api.v1.endpoints import todo
from app.api.v1.endpoints.weportal.customers import (
    router as weportal_customer_router,
)
from app.api.v1.endpoints.weportal.dashboard import router as weportal_dashboard_router
from app.api.v1.endpoints.weportal.my_projects import (
    router as weportal_my_projects_router,
)
from app.api.v1.endpoints.weportal.projects import (
    router as weportal_projects_router,
)
from app.api.v1.endpoints.weportal.locations import (
    router as weportal_locations_router,
)
from app.api.v1.endpoints.weportal import milestones as weportal_milestones
from app.api.v1.endpoints.weportal import tasks as weportal_tasks
from app.api.v1.endpoints.weportal import comments as weportal_comments
from app.api.v1.endpoints.weportal.project_upload import (
    router as weportal_project_upload_router,
)
from app.db.database import engine
from app.models.project_tracking import ProjectScope

app = FastAPI(
    title="PseudoTeam API",
    version="1.0.0",
)


def _ensure_project_scope_date_columns() -> None:
    table_name = ProjectScope.__tablename__
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return

    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
    with engine.begin() as conn:
        if "pscope_startdate" not in existing_cols:
            conn.execute(
                text(
                    f"ALTER TABLE `{table_name}` ADD COLUMN `pscope_startdate` VARCHAR(255) NULL"
                )
            )
        if "pscope_enddate" not in existing_cols:
            conn.execute(
                text(
                    f"ALTER TABLE `{table_name}` ADD COLUMN `pscope_enddate` VARCHAR(255) NULL"
                )
            )


@app.on_event("startup")
def on_startup() -> None:
    _ensure_project_scope_date_columns()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    weportal_auth_router,
    prefix="/api/v1/weportal/auth",
    tags=["WePortal Authentication"],
)

app.include_router(
    dashboard_router,
    prefix="/api/v1/customer",
    tags=["Customer Dashboard"],
)

app.include_router(
    projects,
    prefix="/api/v1/customer",
    tags=["Customer Projects"],
)

app.include_router(
    project_tracking,
    prefix="/api/v1/customer",
    tags=["Project Tracking"],
)

app.include_router(
    critical_spares,
    prefix="/api/v1/customer/critical-spares",
    tags=["Critical Spares"],
)

app.include_router(
    tickets,
    prefix="/api/v1/customer/tickets",
    tags=["Customer Tickets"],
)

app.include_router(
    orders,
    prefix="/api/v1/customer/orders",
    tags=["Customer Orders"],
)

app.include_router(
    checkout_router,
    prefix="/api/v1/customer",
    tags=["Customer Checkout"],
)

app.include_router(
    account,
    prefix="/api/v1/customer/account",
    tags=["Customer Account"],
)

app.include_router(
    comments,
    prefix="/api/v1/customer/comments",
    tags=["Customer Comments"],
)

app.include_router(
    notifications.router,
    prefix="/api/v1/customer",
)

app.include_router(todo.router, prefix="/api/v1")

app.include_router(
    weportal_customer_router,
    prefix="/api/v1/weportal",
    tags=["WePortal Customers"],
)

app.include_router(
    weportal_dashboard_router,
    prefix="/api/v1/weportal/dashboard",
    tags=["WePortal Dashboard"],
)

app.include_router(
    weportal_my_projects_router,
    prefix="/api/v1/weportal/my-projects",
    tags=["WePortal My Projects"],
)

app.include_router(
    weportal_locations_router,
    prefix="/api/v1/weportal/projects",
    tags=["WePortal Project Locations"],
)

app.include_router(
    weportal_projects_router,
    prefix="/api/v1/weportal/projects",
    tags=["WePortal Projects"],
)

app.include_router(
    weportal_project_upload_router,
    prefix="/api/v1/weportal/projects",
    tags=["WePortal Project Upload"],
)

app.include_router(
    weportal_milestones.router,
    prefix="/api/v1/weportal",
    tags=["WePortal Milestones"],
)

app.include_router(
    weportal_tasks.router,
    prefix="/api/v1",
    tags=["WePortal Milestone Tasks"],
)

app.include_router(
    weportal_comments.router,
    prefix="/api/v1/weportal",
    tags=["WePortal Location Comments"],
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "PseudoTeam Python Backend is running",
    }
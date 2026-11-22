from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.weportal.auth import router as weportal_auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.project import router as projects
from app.api.v1.endpoints.project_tracking import router as project_tracking
from app.api.v1.endpoints.critical_spares import router as critical_spares
from app.api.v1.endpoints.tickets import router as tickets
from app.api.v1.endpoints.orders import router as orders
from app.api.v1.endpoints.account import router as account
from app.api.v1.endpoints.comments import router as comments
from app.api.v1.endpoints import notifications
from app.api.v1.endpoints import todo
from app.api.v1.endpoints.weportal.dashboard import router as weportal_dashboard_router
from app.api.v1.endpoints.mom import router as mom_router  # changes done by vb: Minutes of Meeting

app = FastAPI(
    title="PseudoTeam API",
    version="1.0.0",
)

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
    weportal_dashboard_router,
    prefix="/api/v1/weportal/dashboard",
    tags=["WePortal Dashboard"],
)

# changes done by vb: GET /api/v1/customer/projects/{project_id}/moms (read-only MOM for customers)
app.include_router(
    mom_router,
    prefix="/api/v1/customer",
    tags=["Customer Minutes of Meeting"],
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "PseudoTeam Python Backend is running",
    }
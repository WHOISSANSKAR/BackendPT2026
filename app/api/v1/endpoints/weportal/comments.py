from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_weuser
from app.db.database import get_db
from app.models.project import Project
from app.models.project_conversation import ProjectConversation
from app.models.weuser import WeUser

router = APIRouter()


class CreateLocationCommentPayload(BaseModel):
    text: str
    author: str | None = None
    comment_by_cust_id: int | None = None
    comment_by_pt_id: int | None = None
    attachments: str | None = None


def _resolve_project_id(db: Session, project_ref: str) -> int:
    ref = project_ref.strip()
    filters = [Project.plist_projectid == ref]
    if ref.isdigit():
        filters.append(Project.plist_id == int(ref))
    proj = db.execute(select(Project).where(or_(*filters))).scalar_one_or_none()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return proj.plist_id


def _parse_scope_id(location_id: str) -> int:
    raw = location_id.strip()
    if not raw.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid location/scope ID",
        )
    return int(raw)


def _get_weuser_pt_id(current_user: WeUser) -> int | None:
    for attr in ("weuser_id", "id", "user_id", "pt_id"):
        val = getattr(current_user, attr, None)
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
    return None


def _get_weuser_display_name(current_user: WeUser, fallback: str = "Admin") -> str:
    for attr in ("display_name", "name", "full_name", "username", "email"):
        val = getattr(current_user, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return fallback


def _serialize_comment(
    row: ProjectConversation,
    pt_display_name: str,
) -> dict:
    if row.pconv_comment_by_pt_id is not None:
        author = f"{pt_display_name} (#{row.pconv_comment_by_pt_id})"
    elif row.pconv_comment_by_cust_id is not None:
        author = f"Customer #{row.pconv_comment_by_cust_id}"
    else:
        author = pt_display_name

    return {
        "id": str(row.pconv_id),
        "scopeId": row.pconv_scope_id,
        "author": author,
        "text": row.pconv_comment,
        "createdAt": row.pconv_comment_date_time or row.created_at or "",
        "attachments": row.pconv_attachments,
        "readFlag": bool(row.pconv_read_flag),
    }


@router.get("/projects/{project_ref}/locations/{location_id}/comments")
def get_weportal_location_comments(
    project_ref: str = Path(...),
    location_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    _resolve_project_id(db, project_ref)
    scope_id = _parse_scope_id(location_id)

    rows = (
        db.execute(
            select(ProjectConversation)
            .where(ProjectConversation.pconv_scope_id == scope_id)
            .order_by(desc(ProjectConversation.pconv_id))
        )
        .scalars()
        .all()
    )

    pt_name = _get_weuser_display_name(current_user, fallback="WePortal User")
    items = [_serialize_comment(r, pt_display_name=pt_name) for r in rows]

    return {
        "success": True,
        "total": len(items),
        "comments": items,
        "items": items,
    }


@router.post("/projects/{project_ref}/locations/{location_id}/comments")
def post_weportal_location_comments(
    payload: CreateLocationCommentPayload,
    project_ref: str = Path(...),
    location_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: WeUser = Depends(get_current_weuser),
):
    text = payload.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment text cannot be empty",
        )

    _resolve_project_id(db, project_ref)
    scope_id = _parse_scope_id(location_id)

    now_dt_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_short_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    pt_id = payload.comment_by_pt_id
    cust_id = payload.comment_by_cust_id
    if pt_id is None and cust_id is None:
        pt_id = _get_weuser_pt_id(current_user)

    new_row = ProjectConversation(
        pconv_scope_id=scope_id,
        pconv_comment_by_cust_id=cust_id,
        pconv_comment_by_pt_id=pt_id,
        pconv_comment=text,
        pconv_comment_date_time=now_dt_str,
        pconv_attachments=payload.attachments,
        pconv_read_flag=0,
        created_at=now_short_str,
        updated_at=now_short_str,
    )

    db.add(new_row)
    db.commit()
    db.refresh(new_row)

    rows = (
        db.execute(
            select(ProjectConversation)
            .where(ProjectConversation.pconv_scope_id == scope_id)
            .order_by(desc(ProjectConversation.pconv_id))
        )
        .scalars()
        .all()
    )

    pt_name = _get_weuser_display_name(
        current_user,
        fallback=(payload.author or "").strip() or "WePortal User",
    )
    items = [_serialize_comment(r, pt_display_name=pt_name) for r in rows]
    created_item = _serialize_comment(new_row, pt_display_name=pt_name)

    return {
        "success": True,
        "message": "Comment posted successfully.",
        "comment": created_item,
        "comments": items,
    }

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_customer

from app.models.project import Project
from app.models.project_owner import ProjectOwner
from app.models.project_tracking import ProjectScope
from app.models.project_conversation import ProjectConversation


router = APIRouter()


# ---------------------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------------------

class CommentCreate(BaseModel):
    text: str


# ---------------------------------------------------------
# HELPER: CHECK CUSTOMER LOCATION ACCESS
# ---------------------------------------------------------

def get_customer_location(
    db: Session,
    location_id: int,
    customer_id: int,
):
    location = (
        db.query(ProjectScope)
        .join(
            Project,
            Project.plist_id == ProjectScope.pscope_project_id,
        )
        .filter(
            ProjectScope.pscope_id == location_id,
            Project.plist_customer_id == str(customer_id),
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    return location


# ---------------------------------------------------------
# HELPER: FORMAT COMMENT RESPONSE
# ---------------------------------------------------------

def format_comment(
    db: Session,
    comment: ProjectConversation,
):
    author = "Service Provider"
    role = "Service Provider"

    if comment.pconv_comment_by_cust_id is not None:
        customer = (
            db.query(ProjectOwner)
            .filter(
                ProjectOwner.pown_id
                == comment.pconv_comment_by_cust_id
            )
            .first()
        )

        if customer:
            author = customer.pown_name
            role = "Customer"
        else:
            author = "Customer"

    created_at = comment.created_at or comment.pconv_comment_date_time
    updated_at = comment.updated_at

    return {
        "id": str(comment.pconv_id),
        "author": author,
        "role": role,
        "text": comment.pconv_comment,
        "timestamp": comment.pconv_comment_date_time,
        "edited": bool(
            updated_at
            and created_at
            and updated_at != created_at
        ),
    }


# ---------------------------------------------------------
# GET: FETCH COMMENTS FOR A LOCATION
# ---------------------------------------------------------

@router.get("/locations/{location_id}")
def get_location_comments(
    location_id: int,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    # Verify that this location belongs to the logged-in customer.
    get_customer_location(
        db=db,
        location_id=location_id,
        customer_id=current_customer.pown_id,
    )

    comments = (
        db.query(ProjectConversation)
        .filter(
            ProjectConversation.pconv_scope_id == location_id
        )
        .order_by(
            ProjectConversation.pconv_id.desc()
        )
        .all()
    )

    return {
        "success": True,
        "message": "Location comments fetched successfully.",
        "total_comments": len(comments),
        "comments": [
            format_comment(db, comment)
            for comment in comments
        ],
    }


# ---------------------------------------------------------
# POST: ADD A COMMENT
# ---------------------------------------------------------

@router.post("/locations/{location_id}")
def create_location_comment(
    location_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    # Verify location ownership.
    get_customer_location(
        db=db,
        location_id=location_id,
        customer_id=current_customer.pown_id,
    )

    comment_text = payload.text.strip()

    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty.",
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_comment = ProjectConversation(
        pconv_scope_id=location_id,
        pconv_comment_by_cust_id=current_customer.pown_id,
        pconv_comment_by_pt_id=None,
        pconv_comment=comment_text,
        pconv_comment_date_time=now,
        pconv_attachments=None,
        pconv_read_flag=0,
        created_at=now,
        updated_at=now,
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {
        "success": True,
        "message": "Comment added successfully.",
        "comment": format_comment(db, new_comment),
    }


# ---------------------------------------------------------
# PATCH: EDIT A CUSTOMER'S OWN COMMENT
# ---------------------------------------------------------

@router.patch("/{comment_id}")
def update_location_comment(
    comment_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    comment_text = payload.text.strip()

    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty.",
        )

    comment = (
        db.query(ProjectConversation)
        .filter(
            ProjectConversation.pconv_id == comment_id,
            ProjectConversation.pconv_comment_by_cust_id
            == current_customer.pown_id,
        )
        .first()
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or you cannot edit it.",
        )

    # Also verify that the comment belongs to this customer's location.
    get_customer_location(
        db=db,
        location_id=comment.pconv_scope_id,
        customer_id=current_customer.pown_id,
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    comment.pconv_comment = comment_text
    comment.updated_at = now

    db.commit()
    db.refresh(comment)

    return {
        "success": True,
        "message": "Comment updated successfully.",
        "comment": format_comment(db, comment),
    }


# ---------------------------------------------------------
# DELETE: DELETE A CUSTOMER'S OWN COMMENT
# ---------------------------------------------------------

@router.delete("/{comment_id}")
def delete_location_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_customer: ProjectOwner = Depends(
        get_current_customer
    ),
):
    comment = (
        db.query(ProjectConversation)
        .filter(
            ProjectConversation.pconv_id == comment_id,
            ProjectConversation.pconv_comment_by_cust_id
            == current_customer.pown_id,
        )
        .first()
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or you cannot delete it.",
        )

    # Verify location ownership.
    get_customer_location(
        db=db,
        location_id=comment.pconv_scope_id,
        customer_id=current_customer.pown_id,
    )

    db.delete(comment)
    db.commit()

    return {
        "success": True,
        "message": "Comment deleted successfully.",
    }
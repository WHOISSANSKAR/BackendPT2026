# changes done by vb: Minutes of Meeting (MOM) service — read-only list for the customer.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_mom import ProjectMom, ProjectMomActionItem
from app.models.project_tracking import ProjectScope


def _lines(value: str | None) -> list[str]:
    """Multi-value text columns store one entry per line (commas also accepted)."""
    if not value:
        return []
    parts = value.replace("\r", "").split("\n")
    if len(parts) == 1 and "," in parts[0]:
        parts = parts[0].split(",")
    return [p.strip() for p in parts if p.strip()]


def get_project_moms(db: Session, customer_id: str, project_id: int) -> dict:
    """
    Return every MOM recorded for one of the customer's projects, newest meeting first,
    each with its action items in display order.
    """
    project = (
        db.query(Project)
        .filter(
            Project.plist_id == project_id,
            Project.plist_customer_id == str(customer_id),
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    moms = (
        db.query(ProjectMom)
        .filter(ProjectMom.pmom_project_id == project_id)
        .order_by(ProjectMom.pmom_prepared_on.desc(), ProjectMom.pmom_id.desc())
        .all()
    )

    mom_ids = [m.pmom_id for m in moms]
    actions_by_mom: dict[int, list[ProjectMomActionItem]] = {mid: [] for mid in mom_ids}
    if mom_ids:
        actions = (
            db.query(ProjectMomActionItem)
            .filter(ProjectMomActionItem.pmomact_mom_id.in_(mom_ids))
            .order_by(ProjectMomActionItem.pmomact_sort.asc(), ProjectMomActionItem.pmomact_id.asc())
            .all()
        )
        for a in actions:
            actions_by_mom.setdefault(a.pmomact_mom_id, []).append(a)

    scope_ids = {m.pmom_scope_id for m in moms if m.pmom_scope_id}
    scope_names: dict[int, str] = {}
    if scope_ids:
        for s in db.query(ProjectScope).filter(ProjectScope.pscope_id.in_(scope_ids)).all():
            scope_names[s.pscope_id] = ", ".join(x for x in [s.pscope_city, s.pscope_state] if x)

    return {
        "success": True,
        "message": "Meeting minutes fetched successfully",
        "project_id": project_id,
        "total": len(moms),
        "moms": [
            {
                "id": m.pmom_id,
                "project_id": m.pmom_project_id,
                "location_id": m.pmom_scope_id,
                "location": scope_names.get(m.pmom_scope_id) if m.pmom_scope_id else None,
                "phase": m.pmom_phase,
                "milestone": m.pmom_milestone,
                "task": m.pmom_task,
                "prepared_by": m.pmom_prepared_by,
                "prepared_on": m.pmom_prepared_on,
                "meeting_type": m.pmom_meeting_type,
                "attendees_present": _lines(m.pmom_attendees_present),
                "attendees_absent": _lines(m.pmom_attendees_absent),
                "agenda": _lines(m.pmom_agenda),
                "summary": m.pmom_summary,
                "action_items": [
                    {
                        "id": a.pmomact_id,
                        "action": a.pmomact_action,
                        "owner": a.pmomact_owner,
                        "due_date": a.pmomact_due_date,
                        "status": a.pmomact_status or "Open",
                    }
                    for a in actions_by_mom.get(m.pmom_id, [])
                ],
                "next_meeting": m.pmom_next_meeting,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
            }
            for m in moms
        ],
    }

import base64
from datetime import datetime
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.project import Project
from app.models.project_tracking import (
    ProjectScope,
    ProjectPlanner,
    ProjectPlannerTask,
)

logger = logging.getLogger(__name__)

COMPLETED_TASK_STATUSES = ("fullfilled", "fulfilled")

POC_BLOB_CANDIDATE_ATTRS = (
    "pptasks_proof_of_completion",
    "pptasks_proof_completion",
    "pptasks_poc_blob",
    "pptasks_poc_file_blob",
)


def _parse_date_safe(value: str | None) -> datetime | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def is_task_completed(task: ProjectPlannerTask) -> bool:
    pt_status = (getattr(task, "pptasks_pt_status", None) or "").strip().lower()
    sp_status = (getattr(task, "pptasks_sp_status", None) or "").strip().lower()
    return (
        pt_status in COMPLETED_TASK_STATUSES
        or sp_status in COMPLETED_TASK_STATUSES
    )


def _get_raw_poc_blob_value(task: ProjectPlannerTask):
    for attr in POC_BLOB_CANDIDATE_ATTRS:
        if hasattr(task, attr):
            val = getattr(task, attr, None)
            if val is not None:
                return val
    return None


def _normalize_blob_to_bytes(blob_raw) -> bytes:
    if blob_raw is None:
        return b""

    if isinstance(blob_raw, memoryview):
        data = blob_raw.tobytes()
    elif isinstance(blob_raw, bytearray):
        data = bytes(blob_raw)
    elif isinstance(blob_raw, bytes):
        data = blob_raw
    elif isinstance(blob_raw, str):
        s = blob_raw.strip()
        if not s or s.lower() in ("null", "none", "undefined"):
            return b""
        data_uri_match = re.match(r"^data:([^;]+);base64,(.+)$", s, re.DOTALL)
        if data_uri_match:
            try:
                decoded = base64.b64decode(data_uri_match.group(2), validate=False)
                if decoded:
                    return decoded
            except Exception:
                return b""
        try:
            decoded = base64.b64decode(s, validate=True)
            if decoded:
                return decoded
        except Exception:
            pass
        data = s.encode("utf-8", errors="ignore")
    else:
        return b""

    if data.startswith(b"data:"):
        try:
            text = data.decode("utf-8", errors="ignore")
            m = re.match(r"^data:([^;]+);base64,(.+)$", text.strip(), re.DOTALL)
            if m:
                decoded = base64.b64decode(m.group(2), validate=False)
                if decoded:
                    return decoded
        except Exception:
            pass

    return data


def _has_poc_blob(task: ProjectPlannerTask) -> bool:
    raw = _get_raw_poc_blob_value(task)
    if raw is None:
        return False
    normalized = _normalize_blob_to_bytes(raw)
    return len(normalized) > 0


def _extract_task_poc_fields(
    task: ProjectPlannerTask, project_id: int | None = None
) -> dict:
    """
    Extract PoC metadata safely from ProjectPlannerTask.
    Supports BLOB column (`pptasks_proof_of_completion`) and optional URL columns.
    """
    has_blob = _has_poc_blob(task)

    poc_file_url = None
    for attr in (
        "pptasks_proof_completion_url",
        "pptasks_proof_of_completion_url",
        "pptasks_proof_completion_file",
        "pptasks_poc_url",
        "pptasks_poc_file",
    ):
        val = getattr(task, attr, None)
        if val and isinstance(val, str) and val.strip():
            poc_file_url = val.strip()
            break

    poc_available = bool(has_blob or poc_file_url)
    poc_approved = bool(getattr(task, "pptasks_proof_completion_approved", False))
    task_fulfilled = is_task_completed(task)
    can_view_poc = bool(task_fulfilled and poc_available and poc_approved)

    resolved_url = None
    if can_view_poc:
        if has_blob and project_id is not None:
            resolved_url = f"/api/v1/customer/projects/{project_id}/tasks/{task.pptasks_id}/poc"
        else:
            resolved_url = poc_file_url

    poc_file_name = None
    for attr in (
        "pptasks_proof_completion_name",
        "pptasks_poc_file_name",
        "pptasks_poc_name",
    ):
        val = getattr(task, attr, None)
        if val and str(val).strip():
            poc_file_name = str(val).strip()
            break

    if not poc_file_name:
        if poc_file_url:
            poc_file_name = (
                poc_file_url.split("?")[0].split("/")[-1]
                or f"task-{task.pptasks_id}-poc"
            )
        elif has_blob:
            poc_file_name = f"task-{task.pptasks_id}-proof-of-completion"

    poc_notes = None
    for attr in (
        "pptasks_proof_completion_notes",
        "pptasks_poc_remarks",
        "pptasks_poc_notes",
    ):
        val = getattr(task, attr, None)
        if val and str(val).strip():
            poc_notes = str(val).strip()
            break

    return {
        "proof_completion_approved": poc_approved,
        "has_poc_blob": has_blob,
        "poc_available": poc_available,
        "poc_approved": poc_approved,
        "poc_url": resolved_url,
        "poc_file_url": resolved_url,
        "poc_file_name": poc_file_name if can_view_poc else None,
        "poc_notes": poc_notes if can_view_poc else None,
        "can_view_poc": can_view_poc,
    }


def detect_poc_media_type(data: bytes) -> tuple[str, str]:
    """
    Detect MIME type and file extension from magic bytes for BLOB PoC files.
    """
    if data.startswith(b"%PDF-"):
        return "application/pdf", ".pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if data.startswith(b"PK\x03\x04"):
        return "application/zip", ".zip"
    return "application/octet-stream", ".bin"


def get_task_poc_blob_payload(
    db: Session,
    project_id: int,
    customer_id: str,
    task_id: int,
) -> tuple[bytes, str, str] | None:
    """
    Validate project ownership, task fulfillment, PoC presence, and PoC approval,
    then return (raw_bytes, media_type, filename).
    """
    row = (
        db.query(ProjectPlannerTask)
        .join(
            ProjectPlanner,
            ProjectPlannerTask.pptasks_planner_id == ProjectPlanner.pplnr_id,
        )
        .join(
            ProjectScope,
            ProjectPlanner.pplnr_scope_id == ProjectScope.pscope_id,
        )
        .join(Project, ProjectScope.pscope_project_id == Project.plist_id)
        .filter(
            Project.plist_id == project_id,
            Project.plist_customer_id == str(customer_id),
            ProjectPlannerTask.pptasks_id == task_id,
        )
        .first()
    )

    if not row:
        logger.warning(
            "PoC lookup failed: task_id=%s project_id=%s customer_id=%s not found",
            task_id,
            project_id,
            customer_id,
        )
        return None

    poc_meta = _extract_task_poc_fields(row, project_id=project_id)
    if not poc_meta["can_view_poc"] or not poc_meta["has_poc_blob"]:
        logger.warning(
            "PoC not viewable: task_id=%s fulfilled=%s has_blob=%s approved=%s",
            task_id,
            is_task_completed(row),
            poc_meta["has_poc_blob"],
            poc_meta["poc_approved"],
        )
        return None

    blob_raw = _get_raw_poc_blob_value(row)
    raw_bytes = _normalize_blob_to_bytes(blob_raw)
    if not raw_bytes:
        logger.warning("PoC BLOB is empty after normalization for task_id=%s", task_id)
        return None

    media_type, ext = detect_poc_media_type(raw_bytes)
    base_name = poc_meta["poc_file_name"] or f"task-{task_id}-proof-of-completion"
    if not base_name.lower().endswith(ext) and ext != ".bin":
        filename = f"{base_name}{ext}"
    else:
        filename = base_name

    logger.info(
        "Serving PoC BLOB: task_id=%s bytes=%d media_type=%s filename=%s",
        task_id,
        len(raw_bytes),
        media_type,
        filename,
    )
    return raw_bytes, media_type, filename


def calculate_project_progress(db: Session, project_id: int):
    """
    Calculate project progress using the same rules as Laravel.

    Project progress is calculated from:
        Project -> Locations/Scopes -> Milestones -> Tasks

    Task completion:
        fullfilled / fulfilled = 100%
        all other statuses = 0%

    Task weightages are normalized within each milestone.
    """

    scopes = (
        db.query(ProjectScope)
        .filter(ProjectScope.pscope_project_id == project_id)
        .all()
    )

    if not scopes:
        return {
            "overall_progress": 0.0,
            "locations": [],
        }

    total_project_location_progress = 0.0
    location_results = []

    for scope in scopes:

        location_weightage = float(scope.pscope_weightage or 0)

        milestones = (
            db.query(ProjectPlanner)
            .filter(
                ProjectPlanner.pplnr_scope_id == scope.pscope_id
            )
            .all()
        )

        location_milestone_progress = 0.0
        milestone_results = []

        for milestone in milestones:

            milestone_weight = float(
                milestone.pplnr_weightage or 0
            )

            tasks = (
                db.query(ProjectPlannerTask)
                .filter(
                    ProjectPlannerTask.pptasks_planner_id
                    == milestone.pplnr_id
                )
                .all()
            )

            # Calculate total task weightage.
            total_defined_weightage = sum(
                float(task.pptasks_weightage or 0)
                for task in tasks
            )

            # Laravel fallback.
            if total_defined_weightage <= 0:
                total_defined_weightage = 100.0

            milestone_task_progress = 0.0
            task_results = []

            for task in tasks:

                task_weight = float(
                    task.pptasks_weightage or 0
                )

                normalized_task_weight = (
                    task_weight / total_defined_weightage
                ) * 100

                task_progress = (
                    100.0 if is_task_completed(task) else 0.0
                )

                milestone_task_progress += (
                    normalized_task_weight * task_progress
                ) / 100

                poc_fields = _extract_task_poc_fields(
                    task, project_id=project_id
                )

                task_results.append({
                    "id": task.pptasks_id,
                    "title": task.pptasks_task_title,
                    "description": task.pptasks_description,
                    "start_date": task.pptasks_start_date,
                    "end_date": task.pptasks_end_date,
                    "date_of_completion":
                        task.pptasks_date_of_completion,
                    "status": task.pptasks_pt_status,
                    "service_provider_status":
                        task.pptasks_sp_status,
                    "weightage": task_weight,
                    "normalized_weightage": round(
                        normalized_task_weight, 2
                    ),
                    "progress": task_progress,
                    **poc_fields,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                })

            # Milestone progress.
            milestone_progress = round(
                milestone_task_progress, 2
            )

            weighted_milestone_progress = (
                milestone_progress * milestone_weight
            ) / 100

            location_milestone_progress += (
                weighted_milestone_progress
            )

            completed_tasks = sum(
                1 for task in tasks
                if is_task_completed(task)
            )

            milestone_results.append({
                "id": milestone.pplnr_id,
                "name": milestone.pplnr_milestone,
                "description": milestone.pplnr_description,
                "start_date": milestone.pplnr_start_date,
                "end_date": milestone.pplnr_end_date,
                "status": milestone.pplnr_status,
                "weightage": milestone_weight,
                "progress": milestone_progress,
                "weighted_contribution": round(
                    weighted_milestone_progress, 2
                ),
                "total_tasks": len(tasks),
                "completed_tasks": completed_tasks,
                "tasks": task_results,
                "created_at": milestone.created_at,
                "updated_at": milestone.updated_at,
            })

        # Scope/location progress.
        scope_progress = round(
            location_milestone_progress, 2
        )

        scope_weighted_progress = round(
            (scope_progress * location_weightage) / 100,
            2,
        )

        total_project_location_progress += (
            scope_weighted_progress
        )

        completed_milestones = sum(
            1 for milestone in milestone_results
            if milestone["progress"] >= 100
        )

        # Use pscope_startdate / pscope_enddate from project_scope first;
        # fall back to earliest/latest milestone dates if pscope dates are NULL.
        parsed_scope_start = _parse_date_safe(scope.pscope_startdate)
        parsed_scope_end = _parse_date_safe(scope.pscope_enddate)

        if parsed_scope_start:
            location_start_date = parsed_scope_start.strftime("%Y-%m-%d")
        else:
            valid_starts = [
                dt
                for m in milestone_results
                if (dt := _parse_date_safe(m.get("start_date"))) is not None
            ]
            location_start_date = (
                min(valid_starts).strftime("%Y-%m-%d")
                if valid_starts
                else None
            )

        if parsed_scope_end:
            location_end_date = parsed_scope_end.strftime("%Y-%m-%d")
        else:
            valid_ends = [
                dt
                for m in milestone_results
                if (dt := _parse_date_safe(m.get("end_date"))) is not None
            ]
            location_end_date = (
                max(valid_ends).strftime("%Y-%m-%d")
                if valid_ends
                else None
            )

        location_results.append({
            "id": scope.pscope_id,
            "country": scope.pscope_country,
            "state": scope.pscope_state,
            "city": scope.pscope_city,
            "pincode": scope.pscope_pincode,
            "address": scope.pscope_address,
            "status": scope.pscope_status,
            "start_date": location_start_date,
            "end_date": location_end_date,
            "weightage": location_weightage,
            "progress": scope_progress,
            "weighted_contribution": scope_weighted_progress,
            "total_milestones": len(milestones),
            "completed_milestones": completed_milestones,
            "milestones": milestone_results,
            "created_at": scope.created_at,
            "updated_at": scope.updated_at,
        })

    final_progress = round(
        total_project_location_progress, 2
    )

    return {
        "overall_progress": float(final_progress),
        "locations": location_results,
    }


def get_last_updated(project: Project, locations: list) -> str | None:
    """
    Find the latest created_at/updated_at timestamp from the
    project, its locations, milestones and tasks.

    This comparison assumes timestamps use one consistent,
    sortable format, preferably YYYY-MM-DD HH:MM:SS.
    """

    timestamps = [
        getattr(project, "created_at", None),
        getattr(project, "updated_at", None),
    ]

    for location in locations:

        timestamps.extend([
            location.get("created_at"),
            location.get("updated_at"),
        ])

        for milestone in location.get("milestones", []):

            timestamps.extend([
                milestone.get("created_at"),
                milestone.get("updated_at"),
            ])

            for task in milestone.get("tasks", []):

                timestamps.extend([
                    task.get("created_at"),
                    task.get("updated_at"),
                ])

    valid_timestamps = [
        str(timestamp).strip()
        for timestamp in timestamps
        if timestamp and str(timestamp).strip()
    ]

    if not valid_timestamps:
        return None

    return max(valid_timestamps)


def get_tracking_summary(
    db: Session,
    project: Project,
    progress_data: dict | None = None,
):
    """
    Return lightweight data for the horizontal project selector
    and summary cards.

    Pass progress_data when it has already been calculated to
    avoid running the progress queries twice.
    """

    if progress_data is None:
        progress_data = calculate_project_progress(
            db=db,
            project_id=project.plist_id,
        )

    locations = progress_data["locations"]

    all_milestones = [
        milestone
        for location in locations
        for milestone in location["milestones"]
    ]

    total_milestones = len(all_milestones)

    completed_milestones = sum(
        1
        for milestone in all_milestones
        if milestone["progress"] >= 100
    )

    # Determine current phase using milestone status.
    in_progress_milestone = next(
        (
            milestone
            for milestone in all_milestones
            if (milestone.get("status") or "").strip().lower()
            == "in progress"
        ),
        None,
    )

    pending_milestone = next(
        (
            milestone
            for milestone in all_milestones
            if (milestone.get("status") or "").strip().lower()
            not in (
                "completed",
                "complete",
                "in progress",
            )
        ),
        None,
    )

    if in_progress_milestone:
        current_phase = in_progress_milestone["name"]

    elif pending_milestone:
        current_phase = pending_milestone["name"]

    elif all_milestones:
        current_phase = "Completed"

    else:
        current_phase = "Not Started"

    countries = {
        location["country"]
        for location in locations
        if location.get("country")
    }

    return {
        "project_id": project.plist_id,
        "project_code": project.plist_projectid,
        "project_name": project.plist_title,
        "project_status": (
            project.plist_project_status
            or project.plist_status
            or "Not Started"
        ),
        "overall_progress": progress_data["overall_progress"],
        "current_phase": current_phase,
        "total_locations": len(locations),
        "total_countries": len(countries),
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "last_updated": get_last_updated(
            project,
            locations,
        ),
    }


def get_customer_tracking_projects(
    db: Session,
    customer_id: str,
):
    """
    API 1:
    Return lightweight project data for the horizontal slider.
    """

    projects = (
        db.query(Project)
        .filter(
            Project.plist_customer_id == str(customer_id),
            or_(
                Project.plist_status.is_(None),
                Project.plist_status != "Delivered",
            ),
        )
        .order_by(Project.plist_id.desc())
        .all()
    )

    project_results = []

    for project in projects:

        progress_data = calculate_project_progress(
            db=db,
            project_id=project.plist_id,
        )

        summary = get_tracking_summary(
            db=db,
            project=project,
            progress_data=progress_data,
        )

        project_results.append(summary)

    return {
        "success": True,
        "message": "Customer tracking projects fetched successfully",
        "total_projects": len(project_results),
        "projects": project_results,
    }


def get_project_tracking(
    db: Session,
    project: Project,
):
    """
    API 2:
    Return complete data for the selected project.
    """

    progress_data = calculate_project_progress(
        db=db,
        project_id=project.plist_id,
    )

    summary = get_tracking_summary(
        db=db,
        project=project,
        progress_data=progress_data,
    )

    return {
        "success": True,
        "message": "Project tracking data fetched successfully",

        "project": {
            "project_id": project.plist_id,
            "project_code": project.plist_projectid,
            "project_name": project.plist_title,
            "description": project.plist_description,
            "project_type": project.plist_type,
            "category": project.plist_category,
            "customer_name": project.plist_name,
            "customer_email": project.plist_email,
            "contact_number": project.plist_contact,
            "start_date": project.plist_startdate,
            "end_date": project.plist_enddate,
            "currency": project.plist_currency,
            "budget": (
                float(project.plist_budget)
                if project.plist_budget is not None
                else 0.0
            ),
            "final_price": (
                float(project.plist_final_price)
                if project.plist_final_price is not None
                else None
            ),
            "status": project.plist_status,
            "project_status": project.plist_project_status,
            "project_status_description":
                project.plist_project_status_description,
            "project_manager_id": project.plist_pt_mngr_id,
        },

        "overall_progress": summary["overall_progress"],
        "current_phase": summary["current_phase"],
        "total_locations": summary["total_locations"],
        "total_countries": summary["total_countries"],
        "total_milestones": summary["total_milestones"],
        "completed_milestones": summary["completed_milestones"],
        "last_updated": summary["last_updated"],

        "locations": progress_data["locations"],
    }
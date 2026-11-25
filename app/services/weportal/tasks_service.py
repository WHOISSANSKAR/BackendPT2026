import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.weportal.tasks import MilestoneTaskCreate, MilestoneTaskUpdate

MAX_WEIGHTAGE = 100.0


def _normalize_date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = str(value).strip()
    return trimmed if trimmed else None


def _parse_bool_cell(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return default
    text_val = str(value).strip().lower()
    if text_val in {"true", "1", "yes", "y"}:
        return True
    if text_val in {"false", "0", "no", "n", ""}:
        return False
    return default


def _parse_float_cell(value: Any) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = float(value)
        return parsed if parsed == parsed else None
    except (ValueError, TypeError):
        return None


def _extract_tabular_rows(upload_file: UploadFile) -> List[Dict[str, Any]]:
    content = upload_file.file.read()
    filename = (upload_file.filename or "").lower()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if filename.endswith(".csv"):
        decoded = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(decoded))
        return [
            dict(row)
            for row in reader
            if any(str(v or "").strip() for v in row.values())
        ]

    try:
        import openpyxl  # type: ignore

        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)
        headers_raw = next(rows_iter, None)
        if not headers_raw:
            return []

        headers = [str(h or "").strip() for h in headers_raw]
        records: List[Dict[str, Any]] = []
        for row_vals in rows_iter:
            if not row_vals or all(
                v is None or str(v).strip() == "" for v in row_vals
            ):
                continue
            record: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                if header and idx < len(row_vals):
                    record[header] = row_vals[idx]
            records.append(record)
        return records
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Excel parsing requires `openpyxl` on the server, or upload a .csv file.",
        ) from exc


def _verify_milestone_belongs_to_location_and_project(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
) -> None:
    sql = text(
        """
        SELECT p.pplnr_id
        FROM project_planner p
        INNER JOIN project_scope s ON s.pscope_id = p.pplnr_scope_id
        WHERE p.pplnr_id = :milestone_id
          AND p.pplnr_scope_id = :location_id
          AND s.pscope_project_id = :project_id
        LIMIT 1
        """
    )
    row = (
        db.execute(
            sql,
            {
                "milestone_id": milestone_id,
                "location_id": location_id,
                "project_id": project_id,
            },
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Milestone {milestone_id} not found under location {location_id} "
                f"and project {project_id}."
            ),
        )


def _format_task_row(row: Dict[str, Any]) -> Dict[str, Any]:
    weight = (
        float(row["pptasks_weightage"])
        if row.get("pptasks_weightage") is not None
        else 0.0
    )
    return {
        "id": str(row.get("pptasks_id", "")),
        "milestone_id": str(row.get("pptasks_planner_id", "")),
        "title": row.get("pptasks_task_title") or "",
        "description": row.get("pptasks_description") or "",
        "add_weightage": weight > 0,
        "addWeightage": weight > 0,
        "weightage": weight,
        "startDate": str(row["pptasks_start_date"])
        if row.get("pptasks_start_date")
        else None,
        "endDate": str(row["pptasks_end_date"])
        if row.get("pptasks_end_date")
        else None,
        "dueDate": str(row["pptasks_end_date"])
        if row.get("pptasks_end_date")
        else None,
        "createdOn": str(row["created_at"]) if row.get("created_at") else None,
        "dateOfCompletion": str(row["pptasks_date_of_completion"])
        if row.get("pptasks_date_of_completion")
        else None,
        "assignedTo": row.get("pptasks_sp_id") or None,
        "spStatus": row.get("pptasks_sp_status") or "Not Started",
        "status": row.get("pptasks_pt_status") or "Not Started",
        "priority": row.get("pptasks_priority") or "Medium",
        "payment": float(row["pptasks_payment"])
        if row.get("pptasks_payment") is not None
        else None,
        "proofCompletionApproved": int(
            row.get("pptasks_proof_completion_approved") or 0
        ),
        "invoiceRaisedFlag": int(row.get("pptasks_invoice_raised_flag") or 0),
    }


def get_task_weightage_sum(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    exclude_task_id: Optional[int] = None,
    entered_weightage: Optional[float] = None,
) -> Dict[str, Any]:
    _verify_milestone_belongs_to_location_and_project(
        db, project_id, location_id, milestone_id
    )

    if exclude_task_id and exclude_task_id > 0:
        sql = text(
            """
            SELECT COALESCE(SUM(pptasks_weightage), 0) AS total_weightage
            FROM project_planner_tasks
            WHERE pptasks_planner_id = :milestone_id
              AND pptasks_id != :excl_id
            """
        )
        params: Dict[str, Any] = {
            "milestone_id": milestone_id,
            "excl_id": exclude_task_id,
        }
    else:
        sql = text(
            """
            SELECT COALESCE(SUM(pptasks_weightage), 0) AS total_weightage
            FROM project_planner_tasks
            WHERE pptasks_planner_id = :milestone_id
            """
        )
        params = {"milestone_id": milestone_id}

    total_used = round(float(db.execute(sql, params).scalar() or 0.0), 4)
    remaining = round(max(0.0, MAX_WEIGHTAGE - total_used), 4)

    result: Dict[str, Any] = {
        "success": True,
        "total_weightage": total_used,
        "remaining_weightage": remaining,
        "entered_weightage": entered_weightage,
        "projected_total_weightage": None,
        "remaining_after_add": None,
        "exceeds_limit": False,
    }

    if entered_weightage is not None:
        entered_val = round(float(entered_weightage), 4)
        projected = round(total_used + entered_val, 4)
        exceeds = projected > MAX_WEIGHTAGE + 1e-6
        result["entered_weightage"] = entered_val
        result["projected_total_weightage"] = projected
        result["remaining_after_add"] = round(
            max(0.0, MAX_WEIGHTAGE - projected), 4
        )
        result["exceeds_limit"] = exceeds

    return result


def _validate_task_weightage_budget(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    add_weightage: bool,
    weightage: Optional[float],
    exclude_task_id: Optional[int] = None,
) -> float:
    if not add_weightage:
        return 0.0

    if weightage is None or float(weightage) <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task weightage must be greater than 0 when weightage is enabled.",
        )

    val = float(weightage)
    if val > MAX_WEIGHTAGE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task weightage cannot exceed 100%.",
        )

    summary = get_task_weightage_sum(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        exclude_task_id=exclude_task_id,
    )
    existing_total = float(summary["total_weightage"])
    available = float(summary["remaining_weightage"])

    if existing_total >= MAX_WEIGHTAGE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="100% task weightage is already assigned for this milestone.",
        )

    if existing_total + val > MAX_WEIGHTAGE + 1e-6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Weightage {val}% exceeds remaining capacity. "
                f"Assigned: {existing_total}%, Available: {available}%."
            ),
        )

    return round(val, 2)


def list_milestone_tasks(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    _verify_milestone_belongs_to_location_and_project(
        db, project_id, location_id, milestone_id
    )

    sql = """
        SELECT *
        FROM project_planner_tasks
        WHERE pptasks_planner_id = :milestone_id
    """
    params: Dict[str, Any] = {"milestone_id": milestone_id}

    if search and search.strip():
        sql += """
            AND (
                LOWER(COALESCE(pptasks_task_title, '')) LIKE :q
                OR LOWER(COALESCE(pptasks_description, '')) LIKE :q
                OR LOWER(COALESCE(pptasks_sp_id, '')) LIKE :q
                OR LOWER(COALESCE(pptasks_pt_status, '')) LIKE :q
            )
        """
        params["q"] = f"%{search.strip().lower()}%"

    sql += " ORDER BY pptasks_id DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [_format_task_row(dict(r)) for r in rows]


def create_milestone_task(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    payload: MilestoneTaskCreate,
) -> Dict[str, Any]:
    _verify_milestone_belongs_to_location_and_project(
        db, project_id, location_id, milestone_id
    )

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    start_date = _normalize_date(payload.start_date)
    end_date = _normalize_date(payload.end_date or payload.due_date)
    completion_date = _normalize_date(payload.date_of_completion)
    sp_id = payload.sp_id.strip() if payload.sp_id else None

    raw_add = getattr(payload, "add_weightage", None)
    add_weight = (
        bool(raw_add)
        if raw_add is not None
        else (payload.weightage is not None and float(payload.weightage) > 0)
    )

    weightage_val = _validate_task_weightage_budget(
        db=db,
        project_id=project_id,
        location_id=location_id,
        milestone_id=milestone_id,
        add_weightage=add_weight,
        weightage=payload.weightage,
    )

    insert_sql = text(
        """
        INSERT INTO project_planner_tasks (
            pptasks_planner_id,
            pptasks_task_title,
            pptasks_description,
            pptasks_weightage,
            pptasks_start_date,
            pptasks_end_date,
            pptasks_sp_id,
            pptasks_date_of_completion,
            pptasks_sp_status,
            pptasks_pt_status,
            pptasks_payment,
            pptasks_proof_completion_approved,
            pptasks_invoice_raised_flag,
            created_at
        ) VALUES (
            :planner_id,
            :title,
            :description,
            :weightage,
            :start_date,
            :end_date,
            :sp_id,
            :date_of_completion,
            :sp_status,
            :pt_status,
            :payment,
            0,
            0,
            :created_at
        )
        """
    )
    result = db.execute(
        insert_sql,
        {
            "planner_id": milestone_id,
            "title": payload.title.strip(),
            "description": (payload.description or "").strip(),
            "weightage": weightage_val,
            "start_date": start_date,
            "end_date": end_date,
            "sp_id": sp_id,
            "date_of_completion": completion_date,
            "sp_status": payload.sp_status or "Not Started",
            "pt_status": payload.status or "Not Started",
            "payment": payload.payment or 0.0,
            "created_at": now_str,
        },
    )
    db.commit()

    new_id = result.lastrowid
    row = (
        db.execute(
            text("SELECT * FROM project_planner_tasks WHERE pptasks_id = :id"),
            {"id": new_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task created but could not be retrieved.",
        )
    return _format_task_row(dict(row))


def import_milestone_tasks_file(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    upload_file: UploadFile,
) -> Dict[str, Any]:
    _verify_milestone_belongs_to_location_and_project(
        db, project_id, location_id, milestone_id
    )

    raw_rows = _extract_tabular_rows(upload_file)
    if not raw_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task rows found in the uploaded file.",
        )

    created_tasks: List[Dict[str, Any]] = []
    for raw in raw_rows:
        normalized = {
            str(k).strip().lower().replace(" ", "_"): v
            for k, v in raw.items()
            if k is not None
        }

        title = str(
            normalized.get("title")
            or normalized.get("task_title")
            or normalized.get("task_name")
            or ""
        ).strip()
        if not title:
            continue

        weight_val = _parse_float_cell(
            normalized.get("weightage")
            or normalized.get("task_weightage")
            or normalized.get("pptasks_weightage")
        )
        has_add_col = "add_weightage" in normalized and str(
            normalized.get("add_weightage") or ""
        ).strip() != ""
        add_weightage = (
            _parse_bool_cell(normalized.get("add_weightage"))
            if has_add_col
            else bool(weight_val is not None and weight_val > 0)
        )

        row_payload = MilestoneTaskCreate(
            title=title,
            description=str(normalized.get("description") or "").strip(),
            add_weightage=add_weightage,
            weightage=weight_val if add_weightage else 0.0,
            start_date=str(normalized.get("start_date") or "").strip() or None,
            end_date=str(
                normalized.get("end_date") or normalized.get("due_date") or ""
            ).strip()
            or None,
            sp_status=str(
                normalized.get("sp_status")
                or normalized.get("service_partner_status")
                or "Not Started"
            ).strip(),
            status=str(
                normalized.get("pseudo_manager_status")
                or normalized.get("pm_status")
                or normalized.get("status")
                or "Not Started"
            ).strip(),
        )

        created = create_milestone_task(
            db=db,
            project_id=project_id,
            location_id=location_id,
            milestone_id=milestone_id,
            payload=row_payload,
        )
        created_tasks.append(created)

    if not created_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid tasks with a title were found in the file.",
        )

    return {
        "message": f"Imported {len(created_tasks)} tasks successfully.",
        "imported_count": len(created_tasks),
        "tasks": created_tasks,
    }


def update_milestone_task(
    db: Session,
    milestone_id: int,
    task_id: int,
    payload: MilestoneTaskUpdate,
    project_id: Optional[int] = None,
    location_id: Optional[int] = None,
) -> Dict[str, Any]:
    existing = (
        db.execute(
            text(
                """
                SELECT t.*, p.pplnr_scope_id, s.pscope_project_id
                FROM project_planner_tasks t
                INNER JOIN project_planner p ON p.pplnr_id = t.pptasks_planner_id
                INNER JOIN project_scope s ON s.pscope_id = p.pplnr_scope_id
                WHERE t.pptasks_id = :task_id AND t.pptasks_planner_id = :milestone_id
                """
            ),
            {"task_id": task_id, "milestone_id": milestone_id},
        )
        .mappings()
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found for this milestone.",
        )

    resolved_project_id = (
        project_id if project_id is not None else int(existing["pscope_project_id"])
    )
    resolved_location_id = (
        location_id if location_id is not None else int(existing["pplnr_scope_id"])
    )

    updates: Dict[str, Any] = {}
    if payload.title is not None:
        updates["pptasks_task_title"] = payload.title.strip()
    if payload.description is not None:
        updates["pptasks_description"] = payload.description.strip()

    raw_add = getattr(payload, "add_weightage", None)
    if raw_add is not None or payload.weightage is not None:
        existing_weight = float(existing.get("pptasks_weightage") or 0.0)
        next_add = (
            bool(raw_add)
            if raw_add is not None
            else (payload.weightage is not None and float(payload.weightage) > 0)
        )
        candidate_weight = (
            payload.weightage if payload.weightage is not None else existing_weight
        )
        updates["pptasks_weightage"] = _validate_task_weightage_budget(
            db=db,
            project_id=resolved_project_id,
            location_id=resolved_location_id,
            milestone_id=milestone_id,
            add_weightage=next_add,
            weightage=candidate_weight if next_add else 0.0,
            exclude_task_id=task_id,
        )

    if payload.start_date is not None:
        updates["pptasks_start_date"] = _normalize_date(payload.start_date)
    if payload.end_date is not None or payload.due_date is not None:
        updates["pptasks_end_date"] = _normalize_date(
            payload.end_date or payload.due_date
        )
    if payload.sp_id is not None:
        updates["pptasks_sp_id"] = payload.sp_id.strip() or None
    if payload.date_of_completion is not None:
        updates["pptasks_date_of_completion"] = _normalize_date(
            payload.date_of_completion
        )
    if payload.sp_status is not None:
        updates["pptasks_sp_status"] = payload.sp_status
    if payload.status is not None:
        updates["pptasks_pt_status"] = payload.status
    if payload.payment is not None:
        updates["pptasks_payment"] = payload.payment
    if payload.proof_completion_approved is not None:
        updates["pptasks_proof_completion_approved"] = (
            payload.proof_completion_approved
        )
    if payload.invoice_raised_flag is not None:
        updates["pptasks_invoice_raised_flag"] = payload.invoice_raised_flag

    if updates:
        set_clause = ", ".join(f"{col} = :{col}" for col in updates)
        params = {**updates, "task_id": task_id, "milestone_id": milestone_id}
        db.execute(
            text(
                f"""
                UPDATE project_planner_tasks
                SET {set_clause}
                WHERE pptasks_id = :task_id AND pptasks_planner_id = :milestone_id
                """
            ),
            params,
        )
        db.commit()

    updated = (
        db.execute(
            text(
                """
                SELECT * FROM project_planner_tasks
                WHERE pptasks_id = :task_id AND pptasks_planner_id = :milestone_id
                """
            ),
            {"task_id": task_id, "milestone_id": milestone_id},
        )
        .mappings()
        .first()
    )
    return _format_task_row(dict(updated))


def delete_milestone_task(
    db: Session,
    milestone_id: int,
    task_id: int,
) -> None:
    result = db.execute(
        text(
            """
            DELETE FROM project_planner_tasks
            WHERE pptasks_id = :task_id AND pptasks_planner_id = :milestone_id
            """
        ),
        {"task_id": task_id, "milestone_id": milestone_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found for this milestone.",
        )
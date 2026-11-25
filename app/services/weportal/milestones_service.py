from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session


MAX_WEIGHTAGE = 100.0


def _normalize_date_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "nat", "-"):
        return ""
    # Accept YYYY-MM-DD or DD-MM-YYYY
    parts = s.replace("/", "-").split("-")
    if len(parts) == 3:
        if len(parts[0]) == 4:
            return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
        if len(parts[2]) == 4:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return s


def _row_to_milestone_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    ms_id = int(row["pplnr_id"])
    scope_id = int(row["pplnr_scope_id"])
    title = (row.get("pplnr_milestone") or "").strip()
    desc = (row.get("pplnr_description") or "").strip()
    weight = float(row.get("pplnr_weightage") or 0.0)
    start_dt = _normalize_date_str(row.get("pplnr_start_date"))
    end_dt = _normalize_date_str(row.get("pplnr_end_date"))
    st = (row.get("pplnr_status") or "Not Started").strip()
    created = str(row.get("created_at") or "")

    return {
        "id": str(ms_id),
        "pplnr_id": ms_id,
        "pplnr_scope_id": scope_id,
        "title": title,
        "pplnr_milestone": title,
        "description": desc,
        "pplnr_description": desc,
        "add_weightage": weight > 0,
        "weightage": weight,
        "pplnr_weightage": weight,
        "start_date": start_dt,
        "pplnr_start_date": start_dt,
        "end_date": end_dt,
        "pplnr_end_date": end_dt,
        "status": st,
        "pplnr_status": st,
        "created_on": created,
        "created_at": created,
    }


def _verify_location_belongs_to_project(
    db: Session, project_id: int, location_id: int
) -> None:
    sql = text(
        """
        SELECT pscope_id
        FROM project_scope
        WHERE pscope_id = :loc_id AND pscope_project_id = :proj_id
        LIMIT 1
        """
    )
    row = (
        db.execute(sql, {"loc_id": location_id, "proj_id": project_id})
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found under project {project_id}.",
        )


def get_weightage_sum(
    db: Session,
    project_id: int,
    location_id: int,
    exclude_milestone_id: Optional[int] = None,
    entered_weightage: Optional[float] = None,
) -> Dict[str, Any]:
    _verify_location_belongs_to_project(db, project_id, location_id)

    if exclude_milestone_id and exclude_milestone_id > 0:
        sql = text(
            """
            SELECT COALESCE(SUM(pplnr_weightage), 0) AS total_weightage
            FROM project_planner
            WHERE pplnr_scope_id = :loc_id AND pplnr_id != :excl_id
            """
        )
        params = {"loc_id": location_id, "excl_id": exclude_milestone_id}
    else:
        sql = text(
            """
            SELECT COALESCE(SUM(pplnr_weightage), 0) AS total_weightage
            FROM project_planner
            WHERE pplnr_scope_id = :loc_id
            """
        )
        params = {"loc_id": location_id}

    total_used = float(db.execute(sql, params).scalar() or 0.0)
    total_used = round(total_used, 4)
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
        result["remaining_after_add"] = round(max(0.0, MAX_WEIGHTAGE - projected), 4)
        result["exceeds_limit"] = exceeds

    return result


def _validate_weightage_budget(
    db: Session,
    project_id: int,
    location_id: int,
    add_weightage: bool,
    weightage: Optional[float],
    exclude_milestone_id: Optional[int] = None,
) -> float:
    if not add_weightage:
        return 0.0

    if weightage is None or weightage <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Weightage must be greater than 0 when weightage is enabled.",
        )

    summary = get_weightage_sum(
        db=db,
        project_id=project_id,
        location_id=location_id,
        exclude_milestone_id=exclude_milestone_id,
    )
    existing_total = float(summary["total_weightage"])
    available = float(summary["remaining_weightage"])

    if existing_total >= MAX_WEIGHTAGE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="100% milestone weightage is already assigned for this location.",
        )

    if existing_total + float(weightage) > MAX_WEIGHTAGE + 1e-6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Weightage {weightage}% exceeds remaining capacity. "
                f"Assigned: {existing_total}%, Available: {available}%."
            ),
        )

    return round(float(weightage), 2)


def list_milestones(
    db: Session,
    project_id: int,
    location_id: int,
    search: Optional[str] = None,
) -> Tuple[int, List[Dict[str, Any]]]:
    _verify_location_belongs_to_project(db, project_id, location_id)

    if search and search.strip():
        sql = text(
            """
            SELECT *
            FROM project_planner
            WHERE pplnr_scope_id = :loc_id
              AND (
                LOWER(COALESCE(pplnr_milestone, '')) LIKE :q
                OR LOWER(COALESCE(pplnr_description, '')) LIKE :q
                OR LOWER(COALESCE(pplnr_status, '')) LIKE :q
              )
            ORDER BY pplnr_id DESC
            """
        )
        rows = (
            db.execute(
                sql, {"loc_id": location_id, "q": f"%{search.strip().lower()}%"}
            )
            .mappings()
            .all()
        )
    else:
        sql = text(
            """
            SELECT *
            FROM project_planner
            WHERE pplnr_scope_id = :loc_id
            ORDER BY pplnr_id DESC
            """
        )
        rows = db.execute(sql, {"loc_id": location_id}).mappings().all()

    items = [_row_to_milestone_dict(dict(r)) for r in rows]
    return len(items), items


def get_milestone_by_id(
    db: Session, project_id: int, location_id: int, milestone_id: int
) -> Dict[str, Any]:
    _verify_location_belongs_to_project(db, project_id, location_id)
    sql = text(
        """
        SELECT *
        FROM project_planner
        WHERE pplnr_id = :ms_id AND pplnr_scope_id = :loc_id
        LIMIT 1
        """
    )
    row = (
        db.execute(sql, {"ms_id": milestone_id, "loc_id": location_id})
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone {milestone_id} not found.",
        )
    return _row_to_milestone_dict(dict(row))


def create_milestone(
    db: Session, project_id: int, location_id: int, payload: Any
) -> Dict[str, Any]:
    _verify_location_belongs_to_project(db, project_id, location_id)

    final_weight = _validate_weightage_budget(
        db=db,
        project_id=project_id,
        location_id=location_id,
        add_weightage=bool(payload.add_weightage),
        weightage=payload.weightage,
    )

    start_dt = _normalize_date_str(payload.start_date)
    end_dt = _normalize_date_str(payload.end_date)
    st = (payload.status or "Not Started").strip()

    insert_sql = text(
        """
        INSERT INTO project_planner (
            pplnr_scope_id,
            pplnr_milestone,
            pplnr_description,
            pplnr_weightage,
            pplnr_start_date,
            pplnr_end_date,
            pplnr_status,
            created_at
        ) VALUES (
            :scope_id,
            :title,
            :description,
            :weightage,
            :start_date,
            :end_date,
            :status,
            NOW()
        )
        """
    )
    result = db.execute(
        insert_sql,
        {
            "scope_id": location_id,
            "title": payload.title.strip(),
            "description": (payload.description or "").strip(),
            "weightage": final_weight,
            "start_date": start_dt,
            "end_date": end_dt,
            "status": st,
        },
    )
    db.commit()

    new_id = result.lastrowid
    if not new_id:
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    return get_milestone_by_id(db, project_id, location_id, int(new_id))


def update_milestone(
    db: Session,
    project_id: int,
    location_id: int,
    milestone_id: int,
    payload: Any,
) -> Dict[str, Any]:
    existing = get_milestone_by_id(db, project_id, location_id, milestone_id)

    next_title = (
        payload.title.strip()
        if payload.title is not None
        else existing["pplnr_milestone"]
    )
    next_desc = (
        payload.description.strip()
        if payload.description is not None
        else existing["pplnr_description"]
    )
    next_start = (
        _normalize_date_str(payload.start_date)
        if payload.start_date is not None
        else existing["pplnr_start_date"]
    )
    next_end = (
        _normalize_date_str(payload.end_date)
        if payload.end_date is not None
        else existing["pplnr_end_date"]
    )
    next_status = (
        payload.status.strip()
        if payload.status is not None
        else existing["pplnr_status"]
    )

    next_add_weight = (
        bool(payload.add_weightage)
        if payload.add_weightage is not None
        else bool(existing["add_weightage"])
    )
    candidate_weight = (
        payload.weightage
        if payload.weightage is not None
        else float(existing["pplnr_weightage"])
    )

    final_weight = _validate_weightage_budget(
        db=db,
        project_id=project_id,
        location_id=location_id,
        add_weightage=next_add_weight,
        weightage=candidate_weight if next_add_weight else 0.0,
        exclude_milestone_id=milestone_id,
    )

    update_sql = text(
        """
        UPDATE project_planner
        SET
            pplnr_milestone = :title,
            pplnr_description = :description,
            pplnr_weightage = :weightage,
            pplnr_start_date = :start_date,
            pplnr_end_date = :end_date,
            pplnr_status = :status
        WHERE pplnr_id = :ms_id AND pplnr_scope_id = :scope_id
        """
    )
    db.execute(
        update_sql,
        {
            "title": next_title,
            "description": next_desc,
            "weightage": final_weight,
            "start_date": next_start,
            "end_date": next_end,
            "status": next_status,
            "ms_id": milestone_id,
            "scope_id": location_id,
        },
    )
    db.commit()
    return get_milestone_by_id(db, project_id, location_id, milestone_id)


def delete_milestone(
    db: Session, project_id: int, location_id: int, milestone_id: int
) -> None:
    get_milestone_by_id(db, project_id, location_id, milestone_id)
    db.execute(
        text(
            """
            DELETE FROM project_planner
            WHERE pplnr_id = :ms_id AND pplnr_scope_id = :scope_id
            """
        ),
        {"ms_id": milestone_id, "scope_id": location_id},
    )
    db.commit()


def import_milestones_from_excel(
    db: Session, project_id: int, location_id: int, file: UploadFile
) -> Tuple[int, List[Dict[str, Any]]]:
    _verify_location_belongs_to_project(db, project_id, location_id)

    try:
        import openpyxl  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="openpyxl is required to import Excel milestone files.",
        ) from exc

    content = file.file.read()
    wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    headers_raw = next(rows_iter, None)
    if not headers_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded Excel sheet is empty.",
        )

    headers = [str(h or "").strip().lower() for h in headers_raw]

    def col(row_vals: Tuple[Any, ...], names: List[str]) -> Any:
        for name in names:
            if name in headers:
                idx = headers.index(name)
                if idx < len(row_vals):
                    return row_vals[idx]
        return None

    parsed_rows: List[Dict[str, Any]] = []
    batch_weight = 0.0

    for row_vals in rows_iter:
        if not row_vals or all(v is None or str(v).strip() == "" for v in row_vals):
            continue
        title = str(
            col(row_vals, ["milestone", "milestone name", "title", "name"]) or ""
        ).strip()
        if not title:
            continue
        desc = str(col(row_vals, ["description", "desc"]) or "").strip()
        raw_w = col(row_vals, ["weightage", "weight", "pplnr_weightage"])
        w = 0.0
        if raw_w is not None and str(raw_w).strip() != "":
            try:
                w = float(raw_w)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid weightage '{raw_w}' for milestone '{title}'.",
                ) from exc
            if w < 0 or w > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Weightage for '{title}' must be between 0 and 100.",
                )

        batch_weight += w
        parsed_rows.append(
            {
                "title": title,
                "description": desc,
                "weightage": round(w, 2),
                "start_date": _normalize_date_str(
                    col(row_vals, ["start date", "start_date", "startdate"])
                ),
                "end_date": _normalize_date_str(
                    col(row_vals, ["end date", "end_date", "enddate", "due date"])
                ),
                "status": str(col(row_vals, ["status"]) or "Not Started").strip()
                or "Not Started",
            }
        )

    if not parsed_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid milestone rows found in Excel file.",
        )

    summary = get_weightage_sum(db, project_id, location_id)
    existing_total = float(summary["total_weightage"])
    available = float(summary["remaining_weightage"])

    if existing_total + batch_weight > MAX_WEIGHTAGE + 1e-6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Import weightage ({batch_weight}%) plus existing ({existing_total}%) "
                f"exceeds 100%. Available: {available}%."
            ),
        )

    created_items: List[Dict[str, Any]] = []
    insert_sql = text(
        """
        INSERT INTO project_planner (
            pplnr_scope_id,
            pplnr_milestone,
            pplnr_description,
            pplnr_weightage,
            pplnr_start_date,
            pplnr_end_date,
            pplnr_status,
            created_at
        ) VALUES (
            :scope_id,
            :title,
            :description,
            :weightage,
            :start_date,
            :end_date,
            :status,
            NOW()
        )
        """
    )

    for item in parsed_rows:
        res = db.execute(
            insert_sql,
            {
                "scope_id": location_id,
                "title": item["title"],
                "description": item["description"],
                "weightage": item["weightage"],
                "start_date": item["start_date"],
                "end_date": item["end_date"],
                "status": item["status"],
            },
        )
        ms_id = res.lastrowid or db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        created_items.append(
            get_milestone_by_id(db, project_id, location_id, int(ms_id))
        )

    db.commit()
    return len(created_items), created_items
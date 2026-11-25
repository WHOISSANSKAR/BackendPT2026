from datetime import date, datetime
from io import BytesIO

from fastapi import HTTPException, status
from openpyxl import load_workbook
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.project_tracking import ProjectScope
from app.schemas.weportal.locations import (
    LocationImportResponse,
    LocationWeightageSummaryResponse,
    ProjectLocationCreate,
    ProjectLocationListResponse,
    ProjectLocationOut,
    ProjectLocationUpdate,
)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_date_value(val: object) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%d-%m-%Y")
    if isinstance(val, date):
        return val.strftime("%d-%m-%Y")

    cleaned = str(val).strip()
    if not cleaned or cleaned.lower() in {"none", "null", "nat", "nan", "-"}:
        return None

    date_part = cleaned.split("T")[0].split(" ")[0]

    # Direct yyyy-mm-dd -> dd-mm-yyyy (e.g. "2026-11-11" -> "11-11-2026")
    if len(date_part) == 10 and date_part[4] in {"-", "/"} and date_part[7] in {"-", "/"}:
        sep = date_part[4]
        parts = date_part.split(sep)
        if len(parts) == 3 and len(parts[0]) == 4 and len(parts[2]) == 2:
            yyyy, mm, dd = parts
            return f"{dd}-{mm}-{yyyy}"

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_part, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue

    return cleaned


def _to_out(row: ProjectScope) -> ProjectLocationOut:
    weight = (
        float(row.pscope_weightage)
        if row.pscope_weightage is not None
        else None
    )
    start_val = _normalize_date_value(row.pscope_startdate)
    end_val = _normalize_date_value(row.pscope_enddate)
    return ProjectLocationOut(
        id=str(row.pscope_id),
        pscope_id=row.pscope_id,
        pscope_project_id=row.pscope_project_id,
        country=row.pscope_country,
        state=row.pscope_state,
        city=row.pscope_city,
        pincode=row.pscope_pincode,
        address=row.pscope_address,
        startDate=start_val,
        endDate=end_val,
        start_date=start_val,
        end_date=end_val,
        pscope_startdate=start_val,
        pscope_enddate=end_val,
        weightage=weight if weight and weight > 0 else None,
        addWeightage=bool(weight and weight > 0),
        status=row.pscope_status,
        createdOn=row.created_at,
    )


def get_location_weightage_sum(
    db: Session,
    project_id: int,
    exclude_pscope_id: int | None = None,
    entered_weightage: float | None = None,
) -> LocationWeightageSummaryResponse:
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id",
        )

    stmt = select(
        func.coalesce(func.sum(ProjectScope.pscope_weightage), 0)
    ).where(ProjectScope.pscope_project_id == project_id)
    if exclude_pscope_id is not None and exclude_pscope_id > 0:
        stmt = stmt.where(ProjectScope.pscope_id != exclude_pscope_id)

    total = round(float(db.scalar(stmt) or 0.0), 2)
    remaining = max(0.0, round(100.0 - total, 2))

    projected_total: float | None = None
    remaining_after_add: float | None = None
    exceeds_limit = False

    if entered_weightage is not None and entered_weightage > 0:
        entered = round(float(entered_weightage), 2)
        projected_total = round(total + entered, 2)
        remaining_after_add = max(0.0, round(100.0 - projected_total, 2))
        exceeds_limit = projected_total > 100.0

    return LocationWeightageSummaryResponse(
        success=True,
        total_weightage=total,
        remaining_weightage=remaining,
        entered_weightage=entered_weightage,
        projected_total_weightage=projected_total,
        remaining_after_add=remaining_after_add,
        exceeds_limit=exceeds_limit,
    )


def list_project_locations(
    db: Session,
    project_id: int,
    search: str | None = None,
) -> ProjectLocationListResponse:
    stmt = select(ProjectScope).where(
        ProjectScope.pscope_project_id == project_id
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                cast(ProjectScope.pscope_id, String).ilike(term),
                ProjectScope.pscope_country.ilike(term),
                ProjectScope.pscope_state.ilike(term),
                ProjectScope.pscope_city.ilike(term),
                ProjectScope.pscope_startdate.ilike(term),
                ProjectScope.pscope_enddate.ilike(term),
                ProjectScope.pscope_status.ilike(term),
                ProjectScope.pscope_address.ilike(term),
            )
        )

    stmt = stmt.order_by(ProjectScope.pscope_id.desc())
    rows = db.scalars(stmt).all()
    locations = [_to_out(r) for r in rows]
    return ProjectLocationListResponse(
        success=True,
        total=len(locations),
        locations=locations,
    )


def get_project_location(
    db: Session,
    project_id: int,
    location_id: int,
) -> ProjectLocationOut:
    row = db.scalar(
        select(ProjectScope).where(
            ProjectScope.pscope_project_id == project_id,
            ProjectScope.pscope_id == location_id,
        )
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    return _to_out(row)


def create_project_location(
    db: Session,
    project_id: int,
    payload: ProjectLocationCreate,
) -> ProjectLocationOut:
    if payload.add_weightage:
        if payload.pscope_weightage is None or payload.pscope_weightage <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weightage must be a number between 1 and 100.",
            )
        weightage = round(float(payload.pscope_weightage), 2)
    else:
        weightage = 0.0

    if weightage > 0:
        summary = get_location_weightage_sum(db, project_id)
        if round(summary.total_weightage + weightage, 2) > 100.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total weightage cannot exceed 100%. Max allowed: {summary.remaining_weightage}%",
            )

    now = _now_str()
    start_val = _normalize_date_value(payload.resolved_start_date())
    end_val = _normalize_date_value(payload.resolved_end_date())

    row = ProjectScope(
        pscope_project_id=project_id,
        pscope_country=payload.country.strip(),
        pscope_state=payload.state.strip(),
        pscope_city=payload.city.strip(),
        pscope_pincode=payload.pincode.strip(),
        pscope_address=payload.address.strip(),
        pscope_startdate=start_val,
        pscope_enddate=end_val,
        pscope_status=payload.status.strip() or "Not Started",
        pscope_weightage=weightage,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


def update_project_location(
    db: Session,
    project_id: int,
    location_id: int,
    payload: ProjectLocationUpdate,
) -> ProjectLocationOut:
    row = db.scalar(
        select(ProjectScope).where(
            ProjectScope.pscope_project_id == project_id,
            ProjectScope.pscope_id == location_id,
        )
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    if payload.add_weightage is False:
        new_weightage = 0.0
    elif payload.pscope_weightage is not None:
        new_weightage = round(float(payload.pscope_weightage), 2)
    else:
        new_weightage = round(float(row.pscope_weightage or 0.0), 2)

    if new_weightage > 0:
        summary = get_location_weightage_sum(
            db, project_id, exclude_pscope_id=location_id
        )
        if round(summary.total_weightage + new_weightage, 2) > 100.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total weightage cannot exceed 100%. Max allowed: {summary.remaining_weightage}%",
            )

    if payload.country is not None:
        row.pscope_country = payload.country.strip()
    if payload.state is not None:
        row.pscope_state = payload.state.strip()
    if payload.city is not None:
        row.pscope_city = payload.city.strip()
    if payload.pincode is not None:
        row.pscope_pincode = payload.pincode.strip()
    if payload.address is not None:
        row.pscope_address = payload.address.strip()
    if payload.status is not None:
        row.pscope_status = payload.status.strip()

    if payload.has_start_date_update():
        row.pscope_startdate = _normalize_date_value(
            payload.resolved_start_date()
        )
    if payload.has_end_date_update():
        row.pscope_enddate = _normalize_date_value(payload.resolved_end_date())

    row.pscope_weightage = new_weightage
    row.updated_at = _now_str()

    db.commit()
    db.refresh(row)
    return _to_out(row)


def delete_project_location(
    db: Session,
    project_id: int,
    location_id: int,
) -> None:
    row = db.scalar(
        select(ProjectScope).where(
            ProjectScope.pscope_project_id == project_id,
            ProjectScope.pscope_id == location_id,
        )
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    db.delete(row)
    db.commit()


def import_project_locations_excel(
    db: Session,
    project_id: int,
    file_bytes: bytes,
) -> LocationImportResponse:
    wb = load_workbook(filename=BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    header_row = next(rows_iter, None)
    if not header_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded Excel file is empty.",
        )

    headers = [str(h or "").strip().lower() for h in header_row]

    def col_idx(*candidates: str) -> int | None:
        for name in candidates:
            if name in headers:
                return headers.index(name)
        return None

    c_country = col_idx("country", "pscope_country")
    c_state = col_idx("state", "pscope_state")
    c_city = col_idx("city", "pscope_city")
    c_start_date = col_idx(
        "pscope_startdate",
        "start_date",
        "start date",
        "startdate",
        "pscope_start_date",
    )
    c_end_date = col_idx(
        "pscope_enddate",
        "end_date",
        "end date",
        "enddate",
        "pscope_end_date",
    )
    c_pincode = col_idx("pincode", "pin_code", "pin code", "pscope_pincode")
    c_address = col_idx("address", "pscope_address")
    c_weightage = col_idx("weightage", "pscope_weightage")
    c_status = col_idx("status", "pscope_status")

    if c_country is None or c_state is None or c_city is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel must include Country, State, and City columns.",
        )

    existing_weight = get_location_weightage_sum(
        db, project_id
    ).total_weightage
    added_weight = 0.0
    now = _now_str()
    to_insert: list[ProjectScope] = []

    for r in rows_iter:
        if not r or all(
            cell is None or str(cell).strip() == "" for cell in r
        ):
            continue

        country = str(r[c_country] or "").strip()
        state = str(r[c_state] or "").strip()
        city = str(r[c_city] or "").strip()
        if not (country and state and city):
            continue

        start_val = (
            _normalize_date_value(r[c_start_date])
            if c_start_date is not None
            else None
        )
        end_val = (
            _normalize_date_value(r[c_end_date])
            if c_end_date is not None
            else None
        )
        pincode = (
            str(r[c_pincode] or "").strip() if c_pincode is not None else ""
        )
        address = (
            str(r[c_address] or "").strip() if c_address is not None else ""
        )
        status_val = (
            str(r[c_status] or "").strip() if c_status is not None else ""
        ) or "Not Started"
        weight_val = 0.0
        if c_weightage is not None and r[c_weightage] not in (None, ""):
            weight_val = round(float(r[c_weightage]), 2)

        added_weight = round(added_weight + weight_val, 2)
        row = ProjectScope(
            pscope_project_id=project_id,
            pscope_country=country,
            pscope_state=state,
            pscope_city=city,
            pscope_pincode=pincode,
            pscope_address=address,
            pscope_startdate=start_val,
            pscope_enddate=end_val,
            pscope_status=status_val,
            pscope_weightage=weight_val,
            created_at=now,
            updated_at=now,
        )
        to_insert.append(row)

    if round(existing_weight + added_weight, 2) > 100.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imported weightage ({added_weight}%) plus existing ({existing_weight}%) exceeds 100%.",
        )

    db.add_all(to_insert)
    db.commit()

    return LocationImportResponse(
        success=True,
        message=f"Successfully imported {len(to_insert)} locations.",
        imported_count=len(to_insert),
    )
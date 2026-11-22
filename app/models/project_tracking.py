from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
    Float,
)
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProjectScope(Base):
    __tablename__ = "project_scope"

    pscope_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    pscope_project_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    pscope_country: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pscope_state: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pscope_city: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pscope_pincode: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pscope_address: Mapped[str | None] = mapped_column(
        String(400),
        nullable=True,
    )

    pscope_checkrcv: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    pscope_sow: Mapped[bytes | None] = mapped_column(
        LONGBLOB,
        nullable=True,
    )

    pscope_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pscope_weightage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    pscope_startdate: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pscope_enddate: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    updated_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


class ProjectPlanner(Base):
    __tablename__ = "project_planner"

    pplnr_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    pplnr_milestone: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pplnr_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    pplnr_start_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    pplnr_end_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    pplnr_status: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pplnr_scope_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    pplnr_weightage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    updated_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


class ProjectPlannerTask(Base):
    __tablename__ = "project_planner_tasks"

    pptasks_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    pptasks_task_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pptasks_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    pptasks_start_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pptasks_end_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pptasks_date_of_completion: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pptasks_sp_status: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pptasks_pt_status: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pptasks_proof_completion_approved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    pptasks_planner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    pptasks_weightage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    updated_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
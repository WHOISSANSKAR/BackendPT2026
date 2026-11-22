# changes done by vb: Minutes of Meeting (MOM) models — tables created by
# sql/2026-11-22_create_project_mom.sql
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProjectMom(Base):
    __tablename__ = "project_mom"

    pmom_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pmom_project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    pmom_scope_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    pmom_phase: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pmom_milestone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pmom_task: Mapped[str | None] = mapped_column(String(255), nullable=True)

    pmom_prepared_by: Mapped[str] = mapped_column(String(255), nullable=False)
    pmom_prepared_on: Mapped[str] = mapped_column(String(20), nullable=False)
    pmom_meeting_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # one entry per line
    pmom_attendees_present: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmom_attendees_absent: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmom_agenda: Mapped[str | None] = mapped_column(Text, nullable=True)

    pmom_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmom_next_meeting: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pmom_created_by_pt_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)


class ProjectMomActionItem(Base):
    __tablename__ = "project_mom_action_items"

    pmomact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pmomact_mom_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    pmomact_action: Mapped[str] = mapped_column(String(500), nullable=False)
    pmomact_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pmomact_due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pmomact_status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open")
    pmomact_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)

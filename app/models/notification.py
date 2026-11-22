
from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    ntfn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ntfn_notification: Mapped[str] = mapped_column(String(255), nullable=False)
    ntfn_hyperlink: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ntfn_readflag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ntfn_project_id: Mapped[str] = mapped_column(String(400), nullable=False)
    ntfn_forUserId: Mapped[str | None] = mapped_column(String(400), nullable=True)
    ntfn_date_time: Mapped[str] = mapped_column(String(400), nullable=False)
    ntfn_type: Mapped[str] = mapped_column(String(400), nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)

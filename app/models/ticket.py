
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import LargeBinary

from app.db.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    tckt_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    tckt_project_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    tckt_title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    tckt_description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    tckt_date_time: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True
    )

    tckt_status: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default="Open"
    )

    # Deliberately omit tckt_attachment (LONGBLOB).
    tckt_conversation_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    tckt_customer_id: Mapped[str] = mapped_column(
        String(400), nullable=False
    )

    tckt_asgnd_to_pt_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    tckt_asgnd_to_sp_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    created_at: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    updated_at: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    tckt_attachment: Mapped[bytes | None] = mapped_column(
    LargeBinary,
    nullable=True,
    deferred=True,
)

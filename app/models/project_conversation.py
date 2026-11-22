
from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProjectConversation(Base):
    __tablename__ = "project_conversation"

    pconv_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    pconv_scope_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    pconv_comment_by_cust_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    pconv_comment_by_pt_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    pconv_comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    pconv_comment_date_time: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    pconv_attachments: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pconv_read_flag: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    updated_at: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

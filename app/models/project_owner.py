
from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    Text,
    LargeBinary,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProjectOwner(Base):
    __tablename__ = "project_owners"

    pown_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    pown_username: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pown_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pown_user_type: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    pown_country: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_state: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_pincode: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pown_date_of_registration: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pown_about: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    pown_organisation_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_cin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_gstpin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_adhaar: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_body: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_login_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    pown_adhaarfile: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pown_profile_completion_flag: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    pown_dp: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    pown_refered_by: Mapped[str | None] = mapped_column(
        String(400),
        nullable=True,
    )

    pown_promo_code: Mapped[str | None] = mapped_column(
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

    pown_verified: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        default=True,
    )

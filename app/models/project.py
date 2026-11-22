from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Numeric,
)
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Project(Base):
    __tablename__ = "project_list"

    plist_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    plist_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_projectid: Mapped[str] = mapped_column(String(400), nullable=False)
    plist_title: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Uploaded SOW document
    plist_sow: Mapped[bytes | None] = mapped_column(LONGBLOB, nullable=True)

    plist_type: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plist_state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plist_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plist_pincode: Mapped[str | None] = mapped_column(String(255), nullable=True)

    plist_startdate: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_enddate: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_currency: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_budget: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    plist_final_price: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    plist_checkrcv: Mapped[str | None] = mapped_column(String(400), nullable=True)

    plist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_email: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_contact: Mapped[str] = mapped_column(String(255), nullable=False)

    plist_status: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_payment_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    plist_delivered_on: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plist_payment_on: Mapped[str | None] = mapped_column(String(20), nullable=True)

    plist_customeremail: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    plist_project_status: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    plist_ongnew: Mapped[str] = mapped_column(String(255), nullable=False)
    plist_category: Mapped[str] = mapped_column(String(255), nullable=False)

    plist_project_status_description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    plist_coupon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plist_pt_mngr_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    plist_emp_code: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    created_at: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(255), nullable=True)
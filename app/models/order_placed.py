
from decimal import Decimal

from sqlalchemy import BigInteger, Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OrderPlaced(Base):
    __tablename__ = "orders_placed"

    ordplcd_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    ordplcd_hw_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ordplcd_customer_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ordplcd_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ordplcd_qty_placed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ordplcd_no_of_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ordplcd_order_no: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ordplcd_amt: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    ordplcd_status: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ordplcd_delivery_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    ordplcd_order_date: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ordplcd_sp_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ordplcd_final_qty: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    ordplcd_final_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
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

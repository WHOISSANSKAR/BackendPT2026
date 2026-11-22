
from sqlalchemy import BigInteger, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Cart(Base):
    __tablename__ = "cart"

    cart_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cart_order_no: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cart_hw_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cart_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    cart_customer_id: Mapped[str] = mapped_column(String(400), nullable=False)
    cart_hw_amt: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)

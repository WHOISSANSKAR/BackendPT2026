
from sqlalchemy import BigInteger, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Hardware(Base):
    __tablename__ = "hardwares"

    hrdws_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    hrdws_serial_number: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_hw_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_model_number: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_model_description: Mapped[str] = mapped_column(Text, nullable=False)
    hrdws_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    hrdws_family: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_city: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_state: Mapped[str] = mapped_column(String(255), nullable=False)
    hrdws_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    hrdws_sp_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hrdws_sp_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hrdws_hw_status: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)

# changes done by vb
from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OrderAddress(Base):
    __tablename__ = "order_addresses"

    ordradrs_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ordradrs_projectowner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ordradrs_address: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(20), nullable=True)

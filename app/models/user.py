from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    user_type: Mapped[str] = mapped_column(
        String(400), nullable=False
    )
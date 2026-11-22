
from sqlalchemy import Column, Integer, String, Enum
from app.db.database import Base


class Todo(Base):
    __tablename__ = "todo"

    td_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    td_user_id = Column(Integer, nullable=False)
    td_user_type = Column(String(50), nullable=False)
    td_event = Column(String(255), nullable=False)
    td_date = Column(String(400), nullable=False)

    td_status = Column(
        Enum("pending", "completed", name="todo_status"),
        nullable=False,
        default="pending",
        server_default="pending"
    )

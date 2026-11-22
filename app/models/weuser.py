# app/models/weuser.py
from sqlalchemy import Column, Integer, String
from app.db.database import Base


class WeUser(Base):
    __tablename__ = "weusers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False, default="viewer")
    emp_code = Column(String(100), nullable=True)
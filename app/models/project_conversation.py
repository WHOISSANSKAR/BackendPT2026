from sqlalchemy import BigInteger, Column, Integer, String, Text
from app.db.database import Base


class ProjectConversation(Base):
    __tablename__ = "project_conversation"

    pconv_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    pconv_scope_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        nullable=False,
        index=True,
    )
    pconv_comment_by_cust_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        nullable=True,
    )
    pconv_comment_by_pt_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        nullable=True,
    )
    pconv_comment = Column(Text, nullable=False)
    pconv_comment_date_time = Column(String(40), nullable=False)
    pconv_attachments = Column(String(255), nullable=True)
    pconv_read_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from ..core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    t_min = Column(Float, nullable=False)
    t_max = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    celery_task_id = Column(String, nullable=True)
    result_image = Column(Text, nullable=True)   # base64
    max_map = Column(Text, nullable=True)        # base64 compressed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
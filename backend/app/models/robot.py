from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


# ------------------------------
# 机器人角色表
# ------------------------------
class AiRobot(Base):
    __tablename__ = "ai_robots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)  # 客服、技术、幽默等
    personality = Column(Text, nullable=True)  # 性格描述
    response_template = Column(Text, nullable=True)  # 回复模板
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    group_robots = relationship("GroupRobot", back_populates="robot", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="robot", foreign_keys="GroupMessage.robot_id")


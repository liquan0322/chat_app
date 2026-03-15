from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


# ------------------------------
# 用户表
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    individual_conversations = relationship("IndividualConversation", back_populates="user",
                                            cascade="all, delete-orphan")
    conversation_tags = relationship("ConversationTag", back_populates="user", cascade="all, delete-orphan")
    individual_messages = relationship("IndividualMessage", back_populates="user", cascade="all, delete-orphan")
    created_groups = relationship("GroupConversation", back_populates="creator",
                                  foreign_keys="GroupConversation.creator_id")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="sender", foreign_keys="GroupMessage.sender_id")

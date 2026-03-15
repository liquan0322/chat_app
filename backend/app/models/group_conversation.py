from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# ------------------------------
# 群组对话表
# ------------------------------
class GroupConversation(Base):
    __tablename__ = "group_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    creator = relationship("User", back_populates="created_groups")
    group_members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    group_robots = relationship("GroupRobot", back_populates="group", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan")
    conversation_state = relationship("GroupConversationState", back_populates="group", uselist=False,
                                      cascade="all, delete-orphan")


# ------------------------------
# 群组成员表（用户）
# ------------------------------
class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_members")
    user = relationship("User", back_populates="group_memberships")


# ------------------------------
# 群组机器人表
# ------------------------------
class GroupRobot(Base):
    __tablename__ = "group_robots"
    __table_args__ = (
        UniqueConstraint("group_id", "robot_id", name="uq_group_robot"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    robot_id = Column(Integer, ForeignKey("ai_robots.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_robots")
    robot = relationship("AiRobot", back_populates="group_robots")


# ------------------------------
# 群组消息表
# ------------------------------
class GroupMessage(Base):
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL表示机器人
    robot_id = Column(Integer, ForeignKey("ai_robots.id"), nullable=True)  # NULL表示人类用户
    message = Column(Text, nullable=False)
    is_human = Column(Boolean, nullable=False)  # 是否人类发送
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    reply_to_message_id = Column(Integer, ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_messages")
    sender = relationship("User", back_populates="group_messages", foreign_keys=[sender_id])
    robot = relationship("AiRobot", back_populates="group_messages", foreign_keys=[robot_id])
    replied_message = relationship("GroupMessage", remote_side=[id], backref="replies")


# ------------------------------
# 群组对话状态表（用于防机器人循环）
# ------------------------------
class GroupConversationState(Base):
    __tablename__ = "group_conversation_state"

    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), primary_key=True)
    last_human_message_id = Column(Integer, ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)
    consecutive_robot_replies = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    group = relationship("GroupConversation", back_populates="conversation_state")
    last_human_message = relationship("GroupMessage", foreign_keys=[last_human_message_id])
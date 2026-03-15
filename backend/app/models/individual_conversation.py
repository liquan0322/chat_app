from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base



# ------------------------------
# 个人对话表
# ------------------------------
class IndividualConversation(Base):
    __tablename__ = "individual_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    user = relationship("User", back_populates="individual_conversations")
    conversation_tags = relationship("ConversationTag", back_populates="conversation", cascade="all, delete-orphan")
    individual_messages = relationship("IndividualMessage", back_populates="conversation", cascade="all, delete-orphan")



# ------------------------------
# 个人对话标签表
# ------------------------------
class ConversationTag(Base):
    __tablename__ = "conversation_tags"
    __table_args__ = (
        UniqueConstraint("conversation_id", "tag", name="uq_conversation_tag"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("individual_conversations.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 关联关系
    conversation = relationship("IndividualConversation", back_populates="conversation_tags")
    user = relationship("User", back_populates="conversation_tags")


# ------------------------------
# 个人消息表
# ------------------------------
class IndividualMessage(Base):
    __tablename__ = "individual_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("individual_conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    is_user_message = Column(Boolean, nullable=False)
    ai_error = Column(Text, nullable=True)  # 存储AI调用错误信息
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    conversation = relationship("IndividualConversation", back_populates="individual_messages")
    user = relationship("User", back_populates="individual_messages")



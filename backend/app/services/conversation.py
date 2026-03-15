from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app import models, schemas


def create_conversation_tag(
        db: Session,
        conversation_id: UUID,
        tag: str,
        user_id: UUID
):
    """
    为对话添加标签，确保标签唯一且用户只能操作自己的对话
    """
    # 检查对话是否存在且属于当前用户
    conversation = db.query(models.Conversation).filter(
        and_(
            models.Conversation.id == conversation_id,
            models.Conversation.user_id == user_id
        )
    ).first()
    if not conversation:
        raise ValueError("Conversation not found or not owned by user")

    # 检查标签是否已存在
    existing_tag = db.query(models.ConversationTag).filter(
        and_(
            models.ConversationTag.conversation_id == conversation_id,
            models.ConversationTag.tag == tag
        )
    ).first()
    if existing_tag:
        return existing_tag

    # 创建新标签
    db_tag = models.ConversationTag(
        conversation_id=conversation_id,
        tag=tag
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def remove_conversation_tag(
        db: Session,
        conversation_id: UUID,
        tag: str,
        user_id: UUID
) -> bool:
    """
    移除对话的标签
    """
    # 检查权限
    conversation = db.query(models.Conversation).filter(
        and_(
            models.Conversation.id == conversation_id,
            models.Conversation.user_id == user_id
        )
    ).first()
    if not conversation:
        raise ValueError("Conversation not found or not owned by user")

    # 删除标签
    tag_obj = db.query(models.ConversationTag).filter(
        and_(
            models.ConversationTag.conversation_id == conversation_id,
            models.ConversationTag.tag == tag
        )
    ).first()
    if tag_obj:
        db.delete(tag_obj)
        db.commit()
        return True
    return False


def get_conversations_by_tags(
        db: Session,
        user_id: UUID,
        tags: List[str],
        include_all_tags: bool = True
) -> List[models.Conversation]:
    """
    根据标签筛选对话
    - include_all_tags: True=包含所有标签, False=包含任一标签
    """
    query = db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id,
        models.Conversation.is_group == False
    )

    # 关联标签表
    if include_all_tags:
        # 包含所有指定标签
        for tag in tags:
            query = query.join(
                models.ConversationTag,
                models.Conversation.id == models.ConversationTag.conversation_id
            ).filter(models.ConversationTag.tag == tag)
    else:
        # 包含任一指定标签
        query = query.join(
            models.ConversationTag,
            models.Conversation.id == models.ConversationTag.conversation_id
        ).filter(models.ConversationTag.tag.in_(tags))

    # 去重并返回
    return query.distinct().all()
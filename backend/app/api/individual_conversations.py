from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_db
from app.crud.individual_conversation import (
    IndividualConversationCRUD,
    ConversationTagCRUD,
    IndividualMessageCRUD
)
from app.schemas.individual_conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    TagCreate, TagResponse,
    MessageCreate, MessageResponse,
    ResponseModel
)

router = APIRouter(prefix="/conversations", tags=["个人对话管理"])

# ------------------------------
# 对话接口
# ------------------------------
@router.post("", response_model=ResponseModel, summary="创建个人对话")
async def create_conversation(
    conversation_in: ConversationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    conversation, msg = await IndividualConversationCRUD.create_conversation(
        db,
        user_id=conversation_in.user_id,
        title=conversation_in.title
    )
    if not conversation:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=ConversationResponse.from_orm(conversation)
    )

@router.get("/{conversation_id}", response_model=ResponseModel, summary="查询单个对话")
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    conversation = await IndividualConversationCRUD.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ResponseModel(
        code=200,
        message="查询成功",
        data=ConversationResponse.from_orm(conversation)
    )

@router.get("/user/{user_id}", response_model=ResponseModel, summary="查询用户所有对话")
async def get_user_conversations(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    conversations = await IndividualConversationCRUD.get_user_conversations(db, user_id, skip, limit)
    data = [ConversationResponse.from_orm(c) for c in conversations]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=data
    )

@router.put("/{conversation_id}/title", response_model=ResponseModel, summary="更新对话标题")
async def update_conversation_title(
    conversation_id: int,
    conversation_in: ConversationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    conversation, msg = await IndividualConversationCRUD.update_conversation_title(
        db, conversation_id, conversation_in.title
    )
    if not conversation:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=ConversationResponse.from_orm(conversation)
    )

@router.delete("/{conversation_id}", response_model=ResponseModel, summary="删除对话（级联删标签/消息）")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await IndividualConversationCRUD.delete_conversation(db, conversation_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=True
    )

# ------------------------------
# 标签接口
# ------------------------------
@router.post("/tags", response_model=ResponseModel, summary="给对话添加标签")
async def add_conversation_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_async_db)
):
    tag, msg = await ConversationTagCRUD.add_tag_to_conversation(
        db,
        conversation_id=tag_in.conversation_id,
        tag=tag_in.tag,
        user_id=tag_in.user_id
    )
    if not tag:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=TagResponse.from_orm(tag)
    )

@router.get("/{conversation_id}/tags", response_model=ResponseModel, summary="查询对话所有标签")
async def get_conversation_tags(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    tags = await ConversationTagCRUD.get_conversation_tags(db, conversation_id)
    data = [TagResponse.from_orm(t) for t in tags]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=data
    )

@router.get("/user/{user_id}/tags", response_model=ResponseModel, summary="查询用户所有标签（去重）")
async def get_user_tags(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    tags = await ConversationTagCRUD.get_user_tags(db, user_id)
    return ResponseModel(
        code=200,
        message="查询成功",
        data=tags
    )

@router.get("/user/{user_id}/tags/{tag}", response_model=ResponseModel, summary="根据标签查询用户对话")
async def get_conversations_by_tag(
    user_id: int,
    tag: str,
    db: AsyncSession = Depends(get_async_db)
):
    conversations = await ConversationTagCRUD.get_conversations_by_tag(db, user_id, tag)
    data = [ConversationResponse.from_orm(c) for c in conversations]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=data
    )

@router.delete("/{conversation_id}/tags/{tag}", response_model=ResponseModel, summary="删除对话指定标签")
async def delete_conversation_tag(
    conversation_id: int,
    tag: str,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await ConversationTagCRUD.delete_conversation_tag(db, conversation_id, tag)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=True
    )

# ------------------------------
# 消息接口
# ------------------------------
@router.post("/messages", response_model=ResponseModel, summary="发送对话消息")
async def send_message(
    message_in: MessageCreate,
    db: AsyncSession = Depends(get_async_db)
):
    message, msg = await IndividualMessageCRUD.send_message(
        db,
        conversation_id=message_in.conversation_id,
        user_id=message_in.user_id,
        message=message_in.message,
        is_user_message=message_in.is_user_message,
        ai_error=message_in.ai_error
    )
    if not message:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=MessageResponse.from_orm(message)
    )

@router.get("/{conversation_id}/messages", response_model=ResponseModel, summary="查询对话所有消息")
async def get_conversation_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db)
):
    messages = await IndividualMessageCRUD.get_conversation_messages(db, conversation_id, skip, limit)
    data = [MessageResponse.from_orm(m) for m in messages]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=data
    )

@router.delete("/messages/{message_id}", response_model=ResponseModel, summary="删除单条消息")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await IndividualMessageCRUD.delete_message(db, message_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=True
    )
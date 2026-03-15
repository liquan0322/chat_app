from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# ========== 核心：导入日志实例 ==========
from app.core.logging import api_logger, db_logger

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
    # 记录创建对话请求
    api_logger.info(f"接收到创建个人对话请求 - 用户ID：{conversation_in.user_id}，对话标题：{conversation_in.title}")
    try:
        conversation, msg = await IndividualConversationCRUD.create_conversation(
            db,
            user_id=conversation_in.user_id,
            title=conversation_in.title
        )
        if not conversation:
            api_logger.warning(f"创建个人对话失败 - 用户ID：{conversation_in.user_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(
            f"个人对话创建成功 - 对话ID：{conversation.id}，用户ID：{conversation.user_id}，标题：{conversation.title}")
        return ResponseModel(
            code=200,
            message=msg,
            data=ConversationResponse.from_orm(conversation)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"创建个人对话异常 - 用户ID：{conversation_in.user_id}，标题：{conversation_in.title}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="创建个人对话时发生服务器内部错误")


@router.get("/{conversation_id}", response_model=ResponseModel, summary="查询单个对话")
async def get_conversation(
        conversation_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询单个对话请求 - 对话ID：{conversation_id}")
    try:
        conversation = await IndividualConversationCRUD.get_conversation_by_id(db, conversation_id)
        if not conversation:
            api_logger.warning(f"查询单个对话失败 - 对话ID：{conversation_id}，原因：对话不存在")
            raise HTTPException(status_code=404, detail="对话不存在")

        api_logger.info(
            f"查询单个对话成功 - 对话ID：{conversation_id}，用户ID：{conversation.user_id}，标题：{conversation.title}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=ConversationResponse.from_orm(conversation)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"查询单个对话异常 - 对话ID：{conversation_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询单个对话时发生服务器内部错误")


@router.get("/user/{user_id}", response_model=ResponseModel, summary="查询用户所有对话")
async def get_user_conversations(
        user_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询用户所有对话请求 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}")
    try:
        conversations = await IndividualConversationCRUD.get_user_conversations(db, user_id, skip, limit)
        data = [ConversationResponse.from_orm(c) for c in conversations]
        conversation_count = len(data)

        api_logger.info(
            f"查询用户所有对话成功 - 用户ID：{user_id}，共查询到 {conversation_count} 条对话，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询用户所有对话异常 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询用户所有对话时发生服务器内部错误")


@router.put("/{conversation_id}/title", response_model=ResponseModel, summary="更新对话标题")
async def update_conversation_title(
        conversation_id: int,
        conversation_in: ConversationUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到更新对话标题请求 - 对话ID：{conversation_id}，新标题：{conversation_in.title}")
    try:
        conversation, msg = await IndividualConversationCRUD.update_conversation_title(
            db, conversation_id, conversation_in.title
        )
        if not conversation:
            api_logger.warning(f"更新对话标题失败 - 对话ID：{conversation_id}，新标题：{conversation_in.title}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"更新对话标题成功 - 对话ID：{conversation_id}，更新后标题：{conversation.title}")
        return ResponseModel(
            code=200,
            message=msg,
            data=ConversationResponse.from_orm(conversation)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"更新对话标题异常 - 对话ID：{conversation_id}，新标题：{conversation_in.title}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="更新对话标题时发生服务器内部错误")


@router.delete("/{conversation_id}", response_model=ResponseModel, summary="删除对话（级联删标签/消息）")
async def delete_conversation(
        conversation_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除对话请求 - 对话ID：{conversation_id}（级联删除标签/消息）")
    try:
        is_del, msg = await IndividualConversationCRUD.delete_conversation(db, conversation_id)
        if not is_del:
            api_logger.error(f"删除对话失败 - 对话ID：{conversation_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除对话成功 - 对话ID：{conversation_id}（已级联删除关联标签和消息）")
        return ResponseModel(
            code=200,
            message=msg,
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.critical(
            f"删除对话异常 - 对话ID：{conversation_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除对话时发生服务器内部错误")


# ------------------------------
# 标签接口
# ------------------------------
@router.post("/tags", response_model=ResponseModel, summary="给对话添加标签")
async def add_conversation_tag(
        tag_in: TagCreate,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(
        f"接收到给对话添加标签请求 - 对话ID：{tag_in.conversation_id}，用户ID：{tag_in.user_id}，标签：{tag_in.tag}")
    try:
        tag, msg = await ConversationTagCRUD.add_tag_to_conversation(
            db,
            conversation_id=tag_in.conversation_id,
            tag=tag_in.tag,
            user_id=tag_in.user_id
        )
        if not tag:
            api_logger.warning(f"给对话添加标签失败 - 对话ID：{tag_in.conversation_id}，标签：{tag_in.tag}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"给对话添加标签成功 - 标签ID：{tag.id}，对话ID：{tag.conversation_id}，标签：{tag.tag}")
        return ResponseModel(
            code=200,
            message=msg,
            data=TagResponse.from_orm(tag)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"给对话添加标签异常 - 对话ID：{tag_in.conversation_id}，标签：{tag_in.tag}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="给对话添加标签时发生服务器内部错误")


@router.get("/{conversation_id}/tags", response_model=ResponseModel, summary="查询对话所有标签")
async def get_conversation_tags(
        conversation_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询对话所有标签请求 - 对话ID：{conversation_id}")
    try:
        tags = await ConversationTagCRUD.get_conversation_tags(db, conversation_id)
        data = [TagResponse.from_orm(t) for t in tags]
        tag_count = len(data)
        tag_names = [t.tag for t in tags]

        api_logger.info(
            f"查询对话所有标签成功 - 对话ID：{conversation_id}，共查询到 {tag_count} 个标签：{','.join(tag_names)}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询对话所有标签异常 - 对话ID：{conversation_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询对话所有标签时发生服务器内部错误")


@router.get("/user/{user_id}/tags", response_model=ResponseModel, summary="查询用户所有标签（去重）")
async def get_user_tags(
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询用户所有标签请求 - 用户ID：{user_id}（去重）")
    try:
        tags = await ConversationTagCRUD.get_user_tags(db, user_id)
        tag_count = len(tags)

        api_logger.info(f"查询用户所有标签成功 - 用户ID：{user_id}，共查询到 {tag_count} 个唯一标签：{','.join(tags)}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=tags
        )
    except Exception as e:
        api_logger.error(
            f"查询用户所有标签异常 - 用户ID：{user_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询用户所有标签时发生服务器内部错误")


@router.get("/user/{user_id}/tags/{tag}", response_model=ResponseModel, summary="根据标签查询用户对话")
async def get_conversations_by_tag(
        user_id: int,
        tag: str,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到根据标签查询用户对话请求 - 用户ID：{user_id}，标签：{tag}")
    try:
        conversations = await ConversationTagCRUD.get_conversations_by_tag(db, user_id, tag)
        data = [ConversationResponse.from_orm(c) for c in conversations]
        conversation_count = len(data)
        conversation_ids = [str(c.id) for c in conversations]

        api_logger.info(
            f"根据标签查询用户对话成功 - 用户ID：{user_id}，标签：{tag}，共查询到 {conversation_count} 条对话：{','.join(conversation_ids)}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=data
        )
    except Exception as e:
        api_logger.error(
            f"根据标签查询用户对话异常 - 用户ID：{user_id}，标签：{tag}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="根据标签查询用户对话时发生服务器内部错误")


@router.delete("/{conversation_id}/tags/{tag}", response_model=ResponseModel, summary="删除对话指定标签")
async def delete_conversation_tag(
        conversation_id: int,
        tag: str,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除对话指定标签请求 - 对话ID：{conversation_id}，标签：{tag}")
    try:
        is_del, msg = await ConversationTagCRUD.delete_conversation_tag(db, conversation_id, tag)
        if not is_del:
            api_logger.error(f"删除对话指定标签失败 - 对话ID：{conversation_id}，标签：{tag}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除对话指定标签成功 - 对话ID：{conversation_id}，标签：{tag}")
        return ResponseModel(
            code=200,
            message=msg,
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"删除对话指定标签异常 - 对话ID：{conversation_id}，标签：{tag}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除对话指定标签时发生服务器内部错误")


# ------------------------------
# 消息接口
# ------------------------------
@router.post("/messages", response_model=ResponseModel, summary="发送对话消息")
async def send_message(
        message_in: MessageCreate,
        db: AsyncSession = Depends(get_async_db)
):
    # 消息内容脱敏（避免日志过长/敏感信息）
    msg_content = message_in.message[:50] + "..." if len(message_in.message) > 50 else message_in.message
    api_logger.info(
        f"接收到发送对话消息请求 - 对话ID：{message_in.conversation_id}，用户ID：{message_in.user_id}，"
        f"是否用户消息：{message_in.is_user_message}，消息内容：{msg_content}"
    )
    try:
        message, msg = await IndividualMessageCRUD.send_message(
            db,
            conversation_id=message_in.conversation_id,
            user_id=message_in.user_id,
            message=message_in.message,
            is_user_message=message_in.is_user_message,
            ai_error=message_in.ai_error
        )
        if not message:
            api_logger.warning(
                f"发送对话消息失败 - 对话ID：{message_in.conversation_id}，用户ID：{message_in.user_id}，原因：{msg}"
            )
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(
            f"发送对话消息成功 - 消息ID：{message.id}，对话ID：{message.conversation_id}，"
            f"是否用户消息：{message.is_user_message}，AI错误：{message.ai_error}"
        )
        return ResponseModel(
            code=200,
            message=msg,
            data=MessageResponse.from_orm(message)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"发送对话消息异常 - 对话ID：{message_in.conversation_id}，用户ID：{message_in.user_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="发送对话消息时发生服务器内部错误")


@router.get("/{conversation_id}/messages", response_model=ResponseModel, summary="查询对话所有消息")
async def get_conversation_messages(
        conversation_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=200),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询对话所有消息请求 - 对话ID：{conversation_id}，跳过：{skip}，每页条数：{limit}")
    try:
        messages = await IndividualMessageCRUD.get_conversation_messages(db, conversation_id, skip, limit)
        data = [MessageResponse.from_orm(m) for m in messages]
        message_count = len(data)

        api_logger.info(
            f"查询对话所有消息成功 - 对话ID：{conversation_id}，共查询到 {message_count} 条消息，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询对话所有消息异常 - 对话ID：{conversation_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询对话所有消息时发生服务器内部错误")


@router.delete("/messages/{message_id}", response_model=ResponseModel, summary="删除单条消息")
async def delete_message(
        message_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除单条消息请求 - 消息ID：{message_id}")
    try:
        is_del, msg = await IndividualMessageCRUD.delete_message(db, message_id)
        if not is_del:
            api_logger.error(f"删除单条消息失败 - 消息ID：{message_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除单条消息成功 - 消息ID：{message_id}")
        return ResponseModel(
            code=200,
            message=msg,
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"删除单条消息异常 - 消息ID：{message_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除单条消息时发生服务器内部错误")
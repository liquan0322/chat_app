from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union, Dict
from datetime import datetime

# ------------------------------
# 对话相关模型
# ------------------------------
class ConversationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="对话标题")
    user_id: int = Field(..., gt=0, description="所属用户ID")

class ConversationCreate(ConversationBase):
    @validator('title')
    def title_valid(cls, v):
        if not v.strip():
            raise ValueError("对话标题不能全为空格")
        return v.strip()

class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="新对话标题")

class ConversationResponse(ConversationBase):
    id: int = Field(..., description="对话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True
        orm_mode = True

# ------------------------------
# 标签相关模型
# ------------------------------
class TagBase(BaseModel):
    conversation_id: int = Field(..., gt=0, description="对话ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    tag: str = Field(..., min_length=1, max_length=50, description="标签名称")

class TagCreate(TagBase):
    @validator('tag')
    def tag_valid(cls, v):
        return v.strip()

class TagResponse(TagBase):
    id: int = Field(..., description="标签ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        orm_mode = True

# ------------------------------
# 消息相关模型
# ------------------------------
class MessageBase(BaseModel):
    conversation_id: int = Field(..., gt=0, description="对话ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    message: str = Field(..., min_length=1, description="消息内容")
    is_user_message: bool = Field(..., description="是否用户消息")
    ai_error: Optional[str] = Field(None, description="AI错误信息")

class MessageCreate(MessageBase):
    @validator('message')
    def message_valid(cls, v):
        if not v.strip():
            raise ValueError("消息内容不能为空")
        return v

class MessageResponse(MessageBase):
    id: int = Field(..., description="消息ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        orm_mode = True

# ------------------------------
# 通用响应模型
# ------------------------------
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[
        ConversationResponse, List[ConversationResponse],
        TagResponse, List[TagResponse],
        MessageResponse, List[MessageResponse],
        List[str], bool, Dict
    ]] = Field(None, description="返回数据")



# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.db.session import get_async_db
# from app.crud.conversation import IndividualConversationCRUD
# from app.schemas.conversation import (
#     IndividualConversationCreate,
#     IndividualConversationResponse,
#     IndividualConversationQueryParams,
#     IndividualConversationListResponse
# )
#
# router = APIRouter(prefix="/conversations", tags=["个人对话"])
#
# # 异步创建个人对话
# @router.post("/", response_model=IndividualConversationResponse)
# async def create_individual_conversation(
#     conversation_in: IndividualConversationCreate,
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """异步创建个人对话（Pydantic自动验证 + 异步CRUD）"""
#     conversation, msg = await IndividualConversationCRUD.create_conversation(
#         db,
#         user_id=conversation_in.user_id,
#         title=conversation_in.title
#     )
#     if not conversation:
#         raise HTTPException(status_code=400, detail=msg)
#     return conversation
#
# # 异步分页查询个人对话
# @router.get("/", response_model=IndividualConversationListResponse)
# async def list_individual_conversations(
#     params: IndividualConversationQueryParams = Depends(),  # 自动验证查询参数
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """异步分页查询个人对话（支持标签筛选）"""
#     # 异步CRUD查询
#     conversations = await IndividualConversationCRUD.get_user_conversations(
#         db,
#         user_id=params.user_id,
#         skip=params.skip,
#         limit=params.limit
#     )
#     # 若有标签筛选，调用关联查询
#     if params.tag:
#         conversations = await IndividualConversationCRUD.get_conversations_by_tag(
#             db,
#             user_id=params.user_id,
#             tag=params.tag
#         )
#     total = len(conversations)
#     return {
#         "total": total,
#         "skip": params.skip,
#         "limit": params.limit,
#         "items": conversations
#     }
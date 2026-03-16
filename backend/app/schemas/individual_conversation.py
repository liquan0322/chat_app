from pydantic import BaseModel, Field, validator
from pydantic_settings import SettingsConfigDict
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

    model_config = SettingsConfigDict(from_attributes=True)

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

    model_config = SettingsConfigDict(from_attributes=True)

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

    model_config = SettingsConfigDict(from_attributes=True)

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



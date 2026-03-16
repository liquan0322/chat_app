from pydantic import BaseModel, Field, validator
from pydantic_settings import SettingsConfigDict
from typing import Optional, List, Union, Dict
from datetime import datetime

# ------------------------------
# 群组基础模型
# ------------------------------
class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="群组名称")
    creator_id: int = Field(..., gt=0, description="创建者ID")

class GroupCreate(GroupBase):
    @validator('name')
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError("群组名称不能全为空格")
        return v.strip()

class GroupUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="新群组名称")

class GroupResponse(GroupBase):
    id: int = Field(..., description="群组ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = SettingsConfigDict(from_attributes=True)

# ------------------------------
# 群组成员模型
# ------------------------------
class GroupMemberBase(BaseModel):
    group_id: int = Field(..., gt=0, description="群组ID")
    user_id: int = Field(..., gt=0, description="用户ID")

class GroupMemberCreate(GroupMemberBase):
    pass

class GroupMemberResponse(GroupMemberBase):
    id: int = Field(..., description="成员ID")
    created_at: datetime = Field(..., description="加入时间")

    model_config = SettingsConfigDict(from_attributes=True)

# ------------------------------
# 群组机器人模型
# ------------------------------
class GroupRobotBase(BaseModel):
    group_id: int = Field(..., gt=0, description="群组ID")
    robot_id: int = Field(..., gt=0, description="机器人ID")

class GroupRobotCreate(GroupRobotBase):
    pass

class GroupRobotResponse(GroupRobotBase):
    id: int = Field(..., description="关联ID")
    created_at: datetime = Field(..., description="添加时间")

    model_config = SettingsConfigDict(from_attributes=True)

# ------------------------------
# 群组消息模型
# ------------------------------
class GroupMessageBase(BaseModel):
    group_id: int = Field(..., gt=0, description="群组ID")
    message: str = Field(..., min_length=1, description="消息内容")
    is_human: bool = Field(..., description="是否人类消息")
    sender_id: Optional[int] = Field(None, gt=0, description="人类发送者ID")
    robot_id: Optional[int] = Field(None, gt=0, description="机器人ID")
    reply_to_message_id: Optional[int] = Field(None, description="回复的消息ID")

    @validator('message')
    def message_valid(cls, v):
        if not v.strip():
            raise ValueError("消息内容不能为空")
        return v.strip()

    @validator('sender_id', always=True)
    def validate_sender_id(cls, v, values):
        """人类消息必须填sender_id"""
        if values.get('is_human') and not v:
            raise ValueError("人类消息必须指定sender_id")
        return v

    @validator('robot_id', always=True)
    def validate_robot_id(cls, v, values):
        """机器人消息必须填robot_id"""
        if not values.get('is_human') and not v:
            raise ValueError("机器人消息必须指定robot_id")
        return v

class GroupMessageCreate(GroupMessageBase):
    pass

class GroupMessageResponse(GroupMessageBase):
    id: int = Field(..., description="消息ID")
    created_at: datetime = Field(..., description="发送时间")

    model_config = SettingsConfigDict(from_attributes=True)

# ------------------------------
# 群组状态模型
# ------------------------------
class GroupStateBase(BaseModel):
    group_id: int = Field(..., gt=0, description="群组ID")
    consecutive_robot_replies: int = Field(0, ge=0, description="机器人连续回复数")
    last_human_message_id: Optional[int] = Field(None, description="最后人类消息ID")

class GroupStateResponse(GroupStateBase):
    id: int = Field(..., description="状态ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = SettingsConfigDict(from_attributes=True)

# ------------------------------
# 通用响应模型
# ------------------------------
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[
        GroupResponse, List[GroupResponse],
        GroupMemberResponse, List[GroupMemberResponse],
        GroupRobotResponse, List[GroupRobotResponse],
        GroupMessageResponse, List[GroupMessageResponse],
        GroupStateResponse, bool, Dict
    ]] = Field(None, description="返回数据")


from pydantic import BaseModel, Field, validator
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

    class Config:
        from_attributes = True
        orm_mode = True

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

    class Config:
        from_attributes = True
        orm_mode = True

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

    class Config:
        from_attributes = True
        orm_mode = True

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

    class Config:
        from_attributes = True
        orm_mode = True

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
        GroupResponse, List[GroupResponse],
        GroupMemberResponse, List[GroupMemberResponse],
        GroupRobotResponse, List[GroupRobotResponse],
        GroupMessageResponse, List[GroupMessageResponse],
        GroupStateResponse, bool, Dict
    ]] = Field(None, description="返回数据")

# from pydantic import (
#     BaseModel,
#     Field,
#     field_validator,
#     model_validator,
#     ValidationInfo,
# )
# from datetime import datetime
# from typing import Optional, List, Annotated
# from typing_extensions import Self
#
# # ------------------------------
# # 通用类型定义（异步项目复用，减少冗余）
# # ------------------------------
# PositiveInt = Annotated[int, Field(gt=0, description="正整数，必须大于0")]
# NonNegativeInt = Annotated[int, Field(ge=0, description="非负整数，≥0")]
# Str1To100 = Annotated[str, Field(min_length=1, max_length=100, description="1-100个字符")]
#
# # ------------------------------
# # 1. 群组对话（GroupConversation）相关模型
# # ------------------------------
# class GroupConversationBase(BaseModel):
#     """群组对话基础模型（公共字段）"""
#     name: Str1To100
#     creator_id: PositiveInt
#
#     class Config:
#         from_attributes = True  # 支持异步SQLAlchemy ORM对象转换
#         arbitrary_types_allowed = True  # 兼容异步场景特殊类型
#
#
# class GroupConversationCreate(GroupConversationBase):
#     """创建群组对话的验证模型"""
#     pass
#
#
# class GroupConversationUpdate(BaseModel):
#     """更新群组对话的验证模型（仅修改名称）"""
#     name: Optional[Str1To100] = None
#
#     # 新增：避免空更新（异步CRUD优化）
#     @model_validator(mode='before')
#     def check_not_empty(cls, values):
#         if not values:
#             raise ValueError("更新请求不能为空，至少需要传入name字段")
#         return values
#
#
# class GroupConversationResponse(GroupConversationBase):
#     """返回群组对话信息的响应模型"""
#     id: PositiveInt
#     created_at: datetime = Field(..., description="群组创建时间")
#     updated_at: datetime = Field(..., description="群组更新时间")
#
#     # 异步接口常用扩展：嵌套返回群组概要
#     member_count: Optional[NonNegativeInt] = Field(0, description="群成员数量")
#     robot_count: Optional[NonNegativeInt] = Field(0, description="群机器人数量")
#
#
# class GroupConversationListResponse(BaseModel):
#     """批量返回群组对话的响应模型（适配异步分页）"""
#     total: int = Field(..., description="群组总数")
#     skip: NonNegativeInt = Field(..., description="分页偏移量")  # 新增：异步分页必备
#     limit: PositiveInt = Field(..., le=100, description="分页大小（≤100）")  # 新增
#     items: List[GroupConversationResponse] = Field(..., description="群组列表")
#
#
# # ------------------------------
# # 2. 群组成员（GroupMember）相关模型
# # ------------------------------
# class GroupMemberBase(BaseModel):
#     """群组成员基础模型（公共字段）"""
#     group_id: PositiveInt
#     user_id: PositiveInt
#
#     class Config:
#         from_attributes = True
#         arbitrary_types_allowed = True
#
#
# class GroupMemberCreate(GroupMemberBase):
#     """添加群组成员的验证模型"""
#     pass
#
#
# class GroupMemberResponse(GroupMemberBase):
#     """返回群组成员信息的响应模型"""
#     id: PositiveInt
#     joined_at: datetime = Field(..., description="加入时间")
#
#
# class GroupMemberListResponse(BaseModel):
#     """批量返回群组成员的响应模型（适配异步分页）"""
#     total: int = Field(..., description="成员总数")
#     skip: NonNegativeInt = Field(..., description="分页偏移量")
#     limit: PositiveInt = Field(..., le=100, description="分页大小（≤100）")
#     items: List[GroupMemberResponse] = Field(..., description="成员列表")
#     group_id: PositiveInt = Field(..., description="所属群组ID")
#
#
# class BatchAddGroupMembersRequest(BaseModel):
#     """批量添加群组成员的请求模型（增强异步验证）"""
#     group_id: PositiveInt
#     user_ids: List[PositiveInt] = Field(..., min_length=1, description="用户ID列表，至少1个")
#
#     @field_validator('user_ids')
#     def validate_user_ids(cls, v: List[int]) -> List[int]:
#         """验证用户ID为正整数且去重（异步场景避免重复入库）"""
#         unique_user_ids = list(set(v))
#         for user_id in unique_user_ids:
#             if user_id <= 0:
#                 raise ValueError(f"用户ID {user_id} 必须为正整数")
#         return unique_user_ids
#
#     # 新增：限制批量添加数量（避免异步数据库操作过载）
#     @field_validator('user_ids')
#     def validate_user_count(cls, v: List[int]) -> List[int]:
#         if len(v) > 50:
#             raise ValueError("单次批量添加成员最多支持50个用户")
#         return v
#
#
# # ------------------------------
# # 3. 群组机器人（GroupRobot）相关模型
# # ------------------------------
# class GroupRobotBase(BaseModel):
#     """群组机器人基础模型（公共字段）"""
#     group_id: PositiveInt
#     robot_id: PositiveInt
#
#     class Config:
#         from_attributes = True
#         arbitrary_types_allowed = True
#
#
# class GroupRobotCreate(GroupRobotBase):
#     """添加群组机器人的验证模型"""
#     pass
#
#
# class GroupRobotResponse(GroupRobotBase):
#     """返回群组机器人信息的响应模型"""
#     id: PositiveInt
#     added_at: datetime = Field(..., description="添加时间")
#
#
# class GroupRobotListResponse(BaseModel):
#     """批量返回群组机器人的响应模型（适配异步分页）"""
#     total: int = Field(..., description="机器人总数")
#     skip: NonNegativeInt = Field(..., description="分页偏移量")
#     limit: PositiveInt = Field(..., le=20, description="分页大小（≤20）")
#     items: List[GroupRobotResponse] = Field(..., description="机器人列表")
#     group_id: PositiveInt = Field(..., description="所属群组ID")
#
#
# # ------------------------------
# # 4. 群组消息（GroupMessage）相关模型
# # ------------------------------
# class GroupMessageBase(BaseModel):
#     """群组消息基础模型（公共字段）"""
#     group_id: PositiveInt
#     message: Annotated[str, Field(min_length=1, description="消息内容，不能为空")]
#     is_human: bool = Field(..., description="是否人类发送：True-用户，False-机器人")
#     reply_to_message_id: Optional[PositiveInt] = None
#     sender_id: Optional[PositiveInt] = None  # 人类发送者ID
#     robot_id: Optional[PositiveInt] = None  # 机器人发送者ID
#
#     # 修复：适配Pydantic v2的ValidationInfo，增强验证稳定性
#     @field_validator('sender_id', 'robot_id')
#     def validate_sender_exclusivity(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
#         """验证发送方互斥（异步场景避免数据错误）"""
#         is_human = info.data.get('is_human')
#         field_name = info.field_name
#
#         if is_human is None:
#             return v  # 先验证is_human，避免提前报错
#
#         # 人类发送：sender_id必填，robot_id必须为空
#         if is_human:
#             if field_name == 'sender_id' and v is None:
#                 raise ValueError("人类发送消息时，sender_id不能为空")
#             if field_name == 'robot_id' and v is not None:
#                 raise ValueError("人类发送消息时，robot_id必须为空")
#         # 机器人发送：robot_id必填，sender_id必须为空
#         else:
#             if field_name == 'robot_id' and v is None:
#                 raise ValueError("机器人发送消息时，robot_id不能为空")
#             if field_name == 'sender_id' and v is not None:
#                 raise ValueError("机器人发送消息时，sender_id必须为空")
#         return v
#
#     class Config:
#         from_attributes = True
#         arbitrary_types_allowed = True
#
#
# class GroupMessageCreate(GroupMessageBase):
#     """创建群组消息的验证模型"""
#     pass
#
#
# class GroupMessageResponse(GroupMessageBase):
#     """返回群组消息信息的响应模型"""
#     id: PositiveInt
#     created_at: datetime = Field(..., description="消息发送时间")
#
#
# class GroupMessageListResponse(BaseModel):
#     """批量返回群组消息的响应模型（按群组分页）"""
#     total: int = Field(..., description="消息总数")
#     skip: NonNegativeInt = Field(..., description="分页偏移量")
#     limit: PositiveInt = Field(..., le=200, description="分页大小（≤200）")
#     items: List[GroupMessageResponse] = Field(..., description="消息列表")
#     group_id: PositiveInt = Field(..., description="所属群组ID")
#
#
# # ------------------------------
# # 5. 群组对话状态（GroupConversationState）相关模型
# # ------------------------------
# class GroupConversationStateBase(BaseModel):
#     """群组对话状态基础模型（公共字段）"""
#     group_id: PositiveInt  # 主键
#     last_human_message_id: Optional[PositiveInt] = None
#     consecutive_robot_replies: NonNegativeInt = Field(0, description="机器人连续回复次数，默认0")
#
#     class Config:
#         from_attributes = True
#         arbitrary_types_allowed = True
#
#
# class GroupConversationStateCreate(GroupConversationStateBase):
#     """创建群组状态的验证模型"""
#     pass
#
#
# class GroupConversationStateUpdate(BaseModel):
#     """更新群组状态的验证模型（增强异步验证）"""
#     last_human_message_id: Optional[PositiveInt] = None
#     consecutive_robot_replies: Optional[NonNegativeInt] = None
#
#     # 新增：避免空更新（异步CRUD优化）
#     @model_validator(mode='before')
#     def check_not_empty(cls, values):
#         if not values:
#             raise ValueError("更新请求不能为空，至少传入一个状态字段")
#         return values
#
#
# class GroupConversationStateResponse(GroupConversationStateBase):
#     """返回群组状态信息的响应模型"""
#     updated_at: datetime = Field(..., description="状态更新时间")
#
#
# # ------------------------------
# # 异步接口常用查询模型（新增）
# # ------------------------------
# class GroupConversationQueryParams(BaseModel):
#     """群组列表查询参数（适配异步筛选/分页）"""
#     creator_id: Optional[PositiveInt] = None  # 按创建者筛选
#     user_id: Optional[PositiveInt] = None     # 按群成员筛选
#     skip: NonNegativeInt = Field(0, description="分页偏移量，默认0")
#     limit: PositiveInt = Field(10, le=100, description="分页大小，默认10")
#
#
# class GroupMessageQueryParams(BaseModel):
#     """群组消息查询参数（适配异步分页/筛选）"""
#     group_id: PositiveInt  # 必传：群组ID
#     is_human: Optional[bool] = None  # 按发送类型筛选
#     skip: NonNegativeInt = Field(0, description="分页偏移量，默认0")
#     limit: PositiveInt = Field(20, le=200, description="分页大小，默认20")
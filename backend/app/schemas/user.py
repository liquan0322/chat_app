from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Union


# 基础用户模型（公共字段）
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="用户邮箱")


# 创建用户请求模型
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="用户密码（明文）")

    @validator('username')
    def username_valid(cls, v):
        """校验用户名格式"""
        if not v.isalnum() and "_" not in v:
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


# 更新用户请求模型
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码（明文）")


# 用户响应模型（隐藏敏感字段）
class UserResponse(UserBase):
    id: int = Field(..., description="用户ID")

    class Config:
        orm_mode = True  # 支持从ORM对象转换


# 通用响应模型
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[UserResponse, list[UserResponse], bool]] = Field(None, description="返回数据")


# from pydantic import (
#     BaseModel,
#     EmailStr,
#     field_validator,
#     Field,
#     ValidationInfo,
# )
# from datetime import datetime
# from typing import Optional, Annotated
# import re
#
# # ------------------------------
# # 基础模型（公共字段）
# # ------------------------------
# class UserBase(BaseModel):
#     """用户基础模型，包含所有场景都需要的公共字段"""
#     username: str = Field(..., min_length=1, max_length=50, description="用户名，1-50个字符")
#     email: EmailStr = Field(..., description="用户邮箱，需符合邮箱格式")
#
#     class Config:
#         """配置：支持从ORM对象（如SQLAlchemy模型）直接转换为Pydantic模型"""
#         from_attributes = True  # Pydantic v2 替代 orm_mode
#         arbitrary_types_allowed = True  # 兼容异步场景下的ORM对象类型
#
#
# # ------------------------------
# # 创建用户模型（用于注册/新增用户）
# # ------------------------------
# class UserCreate(UserBase):
#     """创建用户时的验证模型（需传入密码）"""
#     password: Annotated[
#         str,
#         Field(..., min_length=8, max_length=100, description="用户密码，8-100个字符")
#     ]
#
#     # 密码复杂度验证（同步，Pydantic验证逻辑无需异步）
#     @field_validator('password')
#     def password_complexity(cls, v: str) -> str:
#         """同步验证密码复杂度（Pydantic验证不建议异步，耗时操作可放接口层）"""
#         if not any(char.isupper() for char in v):
#             raise ValueError('密码必须包含至少一个大写字母')
#         if not any(char.islower() for char in v):
#             raise ValueError('密码必须包含至少一个小写字母')
#         if not any(char.isdigit() for char in v):
#             raise ValueError('密码必须包含至少一个数字')
#         if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
#             raise ValueError('密码必须包含至少一个特殊字符（!@#$%^&*等）')
#         return v
#
#
# # ------------------------------
# # 更新用户模型（用于修改用户信息）
# # ------------------------------
# class UserUpdate(BaseModel):
#     """更新用户时的验证模型（所有字段可选）"""
#     username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名，1-50个字符")
#     email: Optional[EmailStr] = Field(None, description="用户邮箱，需符合邮箱格式")
#     password: Optional[str] = Field(None, min_length=8, max_length=100, description="新密码，8-100个字符")
#
#     # 复用密码复杂度验证（如果更新密码）
#     @field_validator('password')
#     def password_complexity(cls, v: Optional[str]) -> Optional[str]:
#         if v is None:
#             return v  # 未传密码则跳过验证
#         if not any(char.isupper() for char in v):
#             raise ValueError('密码必须包含至少一个大写字母')
#         if not any(char.islower() for char in v):
#             raise ValueError('密码必须包含至少一个小写字母')
#         if not any(char.isdigit() for char in v):
#             raise ValueError('密码必须包含至少一个数字')
#         return v
#
#
# # ------------------------------
# # 响应模型（用于返回给前端的用户信息）
# # ------------------------------
# class UserResponse(UserBase):
#     """返回用户信息的模型（隐藏敏感字段，展示必要字段）"""
#     id: int
#     created_at: datetime
#     updated_at: datetime
#
#     # 注意：这里不包含hashed_password/password，避免敏感信息泄露
#
#
# # ------------------------------
# # 登录验证模型（单独定义）
# # ------------------------------
# class UserLogin(BaseModel):
#     """用户登录时的验证模型"""
#     username: Optional[str] = Field(None, description="用户名或邮箱二选一")
#     email: Optional[EmailStr] = Field(None, description="用户名或邮箱二选一")
#     password: str = Field(..., min_length=8, max_length=100, description="用户密码")
#
#     # 验证：必须传入用户名或邮箱中的一个（适配Pydantic v2的ValidationInfo）
#     @field_validator('username', 'email')
#     def check_login_credential(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
#         # 获取当前验证字段的兄弟字段值
#         other_field = 'email' if info.field_name == 'username' else 'username'
#         other_value = info.data.get(other_field)
#
#         # 如果当前字段和另一个字段都为空，抛出异常
#         if v is None and other_value is None:
#             raise ValueError('必须输入用户名或邮箱中的一个')
#         return v
#
#
# # ------------------------------
# # 异步场景扩展模型（可选）
# # ------------------------------
# class UserLoginResponse(BaseModel):
#     """登录成功后的响应模型（包含token）"""
#     user: UserResponse
#     access_token: str
#     token_type: str = "bearer"
#     expires_at: datetime  # token过期时间
#
#
# class PasswordResetRequest(BaseModel):
#     """密码重置请求模型（异步发送邮件场景）"""
#     email: EmailStr = Field(..., description="注册邮箱")
#
#
# class PasswordResetConfirm(BaseModel):
#     """密码重置确认模型"""
#     token: str = Field(..., description="重置令牌")
#     new_password: str = Field(..., min_length=8, max_length=100, description="新密码")
#
#     @field_validator('new_password')
#     def new_password_complexity(cls, v: str) -> str:
#         """复用密码复杂度验证"""
#         return UserCreate.password_complexity(v)
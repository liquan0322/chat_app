from pydantic import BaseModel, EmailStr, Field, validator
from pydantic_settings import SettingsConfigDict
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

    model_config = SettingsConfigDict(from_attributes=True)


# 通用响应模型
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[UserResponse, list[UserResponse], bool]] = Field(None, description="返回数据")



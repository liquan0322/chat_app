from pydantic import BaseModel, Field, validator
from pydantic_settings import SettingsConfigDict
from typing import Optional, List, Union

# 基础模型（公共字段）
class AiRobotBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="机器人名称")
    role: str = Field(..., min_length=1, max_length=30, description="机器人角色")
    personality: Optional[str] = Field(None, description="性格描述")
    response_template: Optional[str] = Field(None, description="回复模板")

# 创建机器人请求模型
class AiRobotCreate(AiRobotBase):
    # 可选：添加名称格式校验
    @validator('name')
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError("机器人名称不能全为空格")
        return v

# 更新机器人请求模型
class AiRobotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="机器人名称")
    role: Optional[str] = Field(None, min_length=1, max_length=30, description="机器人角色")
    personality: Optional[str] = Field(None, description="性格描述")
    response_template: Optional[str] = Field(None, description="回复模板")

# 机器人响应模型
class AiRobotResponse(AiRobotBase):
    id: int = Field(..., description="机器人ID")

    model_config = SettingsConfigDict(from_attributes=True)


# 通用响应模型
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[AiRobotResponse, List[AiRobotResponse], bool]] = Field(None, description="返回数据")



from pydantic import BaseModel, Field, validator
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

    class Config:
        from_attributes = True  # Pydantic V2 兼容ORM对象
        orm_mode = True         # 兼容Pydantic V1

# 通用响应模型
class ResponseModel(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Union[AiRobotResponse, List[AiRobotResponse], bool]] = Field(None, description="返回数据")


# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.db.session import get_async_db
# from app.crud.robot import AiRobotCRUD  # 你的异步CRUD
#
# router = APIRouter(prefix="/robots", tags=["ai-robots"])
#
# # 异步创建机器人接口
# @router.post("/", response_model=AiRobotResponse)
# async def create_robot(
#     robot_in: AiRobotCreate,  # 直接使用优化后的模型
#     db: AsyncSession = Depends(get_async_db)
# ):
#     robot, msg = await AiRobotCRUD.create_robot(
#         db,
#         name=robot_in.name,
#         role=robot_in.role,  # 枚举自动转为字符串，适配数据库
#         personality=robot_in.personality,
#         response_template=robot_in.response_template
#     )
#     return robot
#
# # 异步分页查询机器人接口
# @router.get("/", response_model=AiRobotListResponse)
# async def list_robots(
#     params: AiRobotQueryParams = Depends(),  # 查询参数自动验证
#     db: AsyncSession = Depends(get_async_db)
# ):
#     # 异步CRUD查询
#     robots = await AiRobotCRUD.get_all_robots(
#         db,
#         skip=params.skip,
#         limit=params.limit
#     )
#     total = len(robots)  # 实际项目中需写count查询
#     return {
#         "total": total,
#         "skip": params.skip,
#         "limit": params.limit,
#         "items": robots
#     }
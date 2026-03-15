from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_db
from app.crud.robot import AiRobotCRUD  # 你的CRUD代码路径
from app.schemas.robot import (
    AiRobotCreate, AiRobotUpdate, AiRobotResponse, ResponseModel
)

# 创建路由
router = APIRouter(prefix="/robots", tags=["AI机器人管理"])

# 1. 创建机器人
@router.post("", response_model=ResponseModel, summary="创建AI机器人")
async def create_robot(
    robot_in: AiRobotCreate,
    db: AsyncSession = Depends(get_async_db)
):
    robot, msg = await AiRobotCRUD.create_robot(
        db=db,
        name=robot_in.name,
        role=robot_in.role,
        personality=robot_in.personality,
        response_template=robot_in.response_template
    )
    if not robot:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=AiRobotResponse.from_orm(robot)
    )

# 2. 根据ID查询机器人
@router.get("/{robot_id}", response_model=ResponseModel, summary="根据ID查询机器人")
async def get_robot_by_id(
    robot_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    robot = await AiRobotCRUD.get_robot_by_id(db, robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    return ResponseModel(
        code=200,
        message="查询成功",
        data=AiRobotResponse.from_orm(robot)
    )

# 3. 根据角色查询机器人
@router.get("/role/{role}", response_model=ResponseModel, summary="根据角色查询机器人")
async def get_robot_by_role(
    role: str,
    db: AsyncSession = Depends(get_async_db)
):
    robots = await AiRobotCRUD.get_robot_by_role(db, role)
    robot_list = [AiRobotResponse.from_orm(r) for r in robots]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=robot_list
    )

# 4. 查询所有机器人（分页）
@router.get("", response_model=ResponseModel, summary="分页查询所有机器人")
async def get_all_robots(
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_async_db)
):
    robots = await AiRobotCRUD.get_all_robots(db, skip=skip, limit=limit)
    robot_list = [AiRobotResponse.from_orm(r) for r in robots]
    return ResponseModel(
        code=200,
        message="查询成功",
        data=robot_list
    )

# 5. 更新机器人
@router.put("/{robot_id}", response_model=ResponseModel, summary="更新机器人信息")
async def update_robot(
    robot_id: int,
    robot_in: AiRobotUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    # 构造更新参数（过滤空值）
    update_kwargs = {}
    if robot_in.name:
        update_kwargs["name"] = robot_in.name
    if robot_in.role:
        update_kwargs["role"] = robot_in.role
    if robot_in.personality is not None:
        update_kwargs["personality"] = robot_in.personality
    if robot_in.response_template is not None:
        update_kwargs["response_template"] = robot_in.response_template

    if not update_kwargs:
        raise HTTPException(status_code=400, detail="请提供要更新的字段")

    robot, msg = await AiRobotCRUD.update_robot(db, robot_id, **update_kwargs)
    if not robot:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=AiRobotResponse.from_orm(robot)
    )

# 6. 删除机器人
@router.delete("/{robot_id}", response_model=ResponseModel, summary="删除机器人")
async def delete_robot(
    robot_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await AiRobotCRUD.delete_robot(db, robot_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200,
        message=msg,
        data=True
    )
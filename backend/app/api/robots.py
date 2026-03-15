from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import api_logger, db_logger
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
    # 记录创建请求（关键信息：机器人名称、角色）
    api_logger.info(f"接收到创建AI机器人请求 - 名称：{robot_in.name}，角色：{robot_in.role}")
    try:
        robot, msg = await AiRobotCRUD.create_robot(
            db=db,
            name=robot_in.name,
            role=robot_in.role,
            personality=robot_in.personality,
            response_template=robot_in.response_template
        )
        if not robot:
            api_logger.warning(f"创建AI机器人失败 - 名称：{robot_in.name}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"AI机器人创建成功 - 机器人ID：{robot.id}，名称：{robot.name}，角色：{robot.role}")
        return ResponseModel(
            code=200,
            message=msg,
            data=AiRobotResponse.from_orm(robot)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"创建AI机器人异常 - 名称：{robot_in.name}，角色：{robot_in.role}，异常信息：{str(e)}",
            exc_info=True  # 记录完整异常堆栈
        )
        raise HTTPException(status_code=500, detail="创建AI机器人时发生服务器内部错误")


# 2. 根据ID查询机器人
@router.get("/{robot_id}", response_model=ResponseModel, summary="根据ID查询机器人")
async def get_robot_by_id(
        robot_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询AI机器人请求 - 机器人ID：{robot_id}")
    try:
        robot = await AiRobotCRUD.get_robot_by_id(db, robot_id)
        if not robot:
            api_logger.warning(f"查询AI机器人失败 - 机器人ID：{robot_id}，原因：机器人不存在")
            raise HTTPException(status_code=404, detail="机器人不存在")

        api_logger.info(f"查询AI机器人成功 - 机器人ID：{robot_id}，名称：{robot.name}，角色：{robot.role}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=AiRobotResponse.from_orm(robot)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"查询AI机器人异常 - 机器人ID：{robot_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询AI机器人时发生服务器内部错误")


# 3. 根据名字查询机器人
@router.get("/role/{role}", response_model=ResponseModel, summary="根据角色查询机器人")
async def get_robot_by_role(
        role: str,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到按角色查询AI机器人请求 - 角色：{role}")
    try:
        robots = await AiRobotCRUD.get_robot_by_role(db, role)
        robot_list = [AiRobotResponse.from_orm(r) for r in robots]
        robot_count = len(robot_list)

        api_logger.info(f"按角色查询AI机器人成功 - 角色：{role}，查询到 {robot_count} 个机器人")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=robot_list
        )
    except Exception as e:
        api_logger.error(
            f"按角色查询AI机器人异常 - 角色：{role}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="按角色查询AI机器人时发生服务器内部错误")


# 4. 查询所有机器人（分页）
@router.get("", response_model=ResponseModel, summary="分页查询所有机器人")
async def get_all_robots(
        skip: int = Query(0, ge=0, description="跳过条数"),
        limit: int = Query(10, ge=1, le=100, description="每页条数"),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到分页查询所有AI机器人请求 - 跳过：{skip}，每页条数：{limit}")
    try:
        robots = await AiRobotCRUD.get_all_robots(db, skip=skip, limit=limit)
        robot_list = [AiRobotResponse.from_orm(r) for r in robots]
        robot_count = len(robot_list)

        api_logger.info(f"分页查询AI机器人成功 - 共查询到 {robot_count} 个机器人，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=robot_list
        )
    except Exception as e:
        api_logger.error(
            f"分页查询AI机器人异常 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="分页查询AI机器人时发生服务器内部错误")


# 5. 更新机器人
@router.put("/{robot_id}", response_model=ResponseModel, summary="更新机器人信息")
async def update_robot(
        robot_id: int,
        robot_in: AiRobotUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    # 整理要更新的字段（便于日志记录）
    update_fields = []
    if robot_in.name:
        update_fields.append("名称")
    if robot_in.role:
        update_fields.append("角色")
    if robot_in.personality is not None:
        update_fields.append("性格设定")
    if robot_in.response_template is not None:
        update_fields.append("回复模板")

    api_logger.info(f"接收到更新AI机器人请求 - 机器人ID：{robot_id}，更新字段：{','.join(update_fields)}")
    try:
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
            api_logger.warning(f"更新AI机器人失败 - 机器人ID：{robot_id}，原因：未提供要更新的字段")
            raise HTTPException(status_code=400, detail="请提供要更新的字段")

        robot, msg = await AiRobotCRUD.update_robot(db, robot_id, **update_kwargs)
        if not robot:
            api_logger.warning(f"更新AI机器人失败 - 机器人ID：{robot_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"更新AI机器人成功 - 机器人ID：{robot_id}，更新后名称：{robot.name}，角色：{robot.role}")
        return ResponseModel(
            code=200,
            message=msg,
            data=AiRobotResponse.from_orm(robot)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"更新AI机器人异常 - 机器人ID：{robot_id}，更新字段：{','.join(update_fields)}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="更新AI机器人时发生服务器内部错误")


# 6. 删除机器人
@router.delete("/{robot_id}", response_model=ResponseModel, summary="删除机器人")
async def delete_robot(
        robot_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除AI机器人请求 - 机器人ID：{robot_id}（物理删除）")
    try:
        is_del, msg = await AiRobotCRUD.delete_robot(db, robot_id)
        if not is_del:
            api_logger.error(f"删除AI机器人失败 - 机器人ID：{robot_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除AI机器人成功 - 机器人ID：{robot_id}")
        return ResponseModel(
            code=200,
            message=msg,
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.critical(
            f"删除AI机器人异常 - 机器人ID：{robot_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除AI机器人时发生服务器内部错误")
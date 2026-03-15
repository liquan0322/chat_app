from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

# ========== 核心：导入日志实例 ==========
from app.core.logging import logger, api_logger, db_logger

from app.db.session import get_async_db
from app.crud.user import UserCRUD
from app.schemas.user import UserCreate, UserUpdate, UserResponse, ResponseModel
from app.core.security import get_password_hash

# 创建路由实例
router = APIRouter(prefix="/users", tags=["用户管理"])


# 1. 创建用户接口
@router.post(
    "",
    response_model=ResponseModel,
    summary="创建新用户",
    description="创建新用户，密码会自动加密存储"
)
async def create_user(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_async_db)
):
    # 记录接口请求（脱敏：不记录原始密码）
    api_logger.info(f"接收到创建用户请求 - 用户名：{user_in.username}，邮箱：{user_in.email}")
    try:
        # 加密密码
        hashed_password = get_password_hash(user_in.password)
        db_logger.debug(f"用户 {user_in.username} 密码加密完成")

        # 调用CRUD创建用户
        user, msg = await UserCRUD.create_user(
            db=db,
            username=user_in.username,
            hashed_password=hashed_password,
            email=user_in.email
        )

        if not user:
            api_logger.warning(f"创建用户失败 - 用户名：{user_in.username}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"用户创建成功 - 用户ID：{user.id}，用户名：{user.username}")
        return ResponseModel(
            code=200,
            message=msg,
            data=UserResponse.from_orm(user)
        )
    except Exception as e:
        # 记录异常（含堆栈）
        api_logger.error(f"创建用户异常 - 用户名：{user_in.username}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建用户时发生服务器内部错误")


# 2. 根据ID查询用户
@router.get(
    "/{user_id}",
    response_model=ResponseModel,
    summary="根据ID查询用户",
    description="根据用户ID获取用户详情"
)
async def get_user_by_id(
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询用户请求 - 用户ID：{user_id}")
    try:
        user = await UserCRUD.get_user_by_id(db, user_id)
        if not user:
            api_logger.warning(f"查询用户失败 - 用户ID：{user_id}，原因：用户不存在")
            raise HTTPException(status_code=404, detail="用户不存在")

        api_logger.info(f"查询用户成功 - 用户ID：{user_id}，用户名：{user.username}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=UserResponse.from_orm(user)
        )
    except HTTPException:
        # 已知的404异常无需重复记录堆栈
        raise
    except Exception as e:
        api_logger.error(f"查询用户异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询用户时发生服务器内部错误")


# 3. 根据用户名查询用户
@router.get(
    "/username/{username}",
    response_model=ResponseModel,
    summary="根据用户名查询用户",
    description="根据用户名获取用户详情"
)
async def get_user_by_username(
        username: str,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询用户请求 - 用户名：{username}")
    try:
        user = await UserCRUD.get_user_by_username(db, username)
        if not user:
            api_logger.warning(f"查询用户失败 - 用户名：{username}，原因：用户不存在")
            raise HTTPException(status_code=404, detail="用户不存在")

        api_logger.info(f"查询用户成功 - 用户名：{username}，用户ID：{user.id}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=UserResponse.from_orm(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"查询用户异常 - 用户名：{username}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询用户时发生服务器内部错误")


# 4. 查询所有用户（分页）
@router.get(
    "",
    response_model=ResponseModel,
    summary="查询所有用户",
    description="分页查询所有用户列表"
)
async def get_all_users(
        skip: int = Query(0, ge=0, description="跳过条数"),
        limit: int = Query(10, ge=1, le=100, description="每页条数"),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到分页查询用户请求 - 跳过：{skip}，每页条数：{limit}")
    try:
        users = await UserCRUD.get_all_users(db, skip=skip, limit=limit)
        user_count = len(users)

        # 转换为响应模型列表
        user_list = [UserResponse.from_orm(user) for user in users]

        api_logger.info(f"分页查询用户成功 - 共查询到 {user_count} 条用户数据，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200,
            message="查询成功",
            data=user_list
        )
    except Exception as e:
        api_logger.error(f"分页查询用户异常 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="分页查询用户时发生服务器内部错误")


# 5. 更新用户信息
@router.put(
    "/{user_id}",
    response_model=ResponseModel,
    summary="更新用户信息",
    description="根据用户ID更新用户信息（支持用户名、邮箱、密码）"
)
async def update_user(
        user_id: int,
        user_in: UserUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    # 记录更新请求（脱敏：不记录原始密码）
    update_fields = []
    if user_in.username:
        update_fields.append("用户名")
    if user_in.email:
        update_fields.append("邮箱")
    if user_in.password:
        update_fields.append("密码")

    api_logger.info(f"接收到更新用户请求 - 用户ID：{user_id}，更新字段：{','.join(update_fields)}")

    try:
        # 构造更新参数（过滤空值）
        update_kwargs = {}
        if user_in.username:
            update_kwargs["username"] = user_in.username
        if user_in.email:
            update_kwargs["email"] = user_in.email
        if user_in.password:
            update_kwargs["hashed_password"] = get_password_hash(user_in.password)
            db_logger.debug(f"用户 {user_id} 密码更新 - 已加密新密码")

        if not update_kwargs:
            api_logger.warning(f"更新用户失败 - 用户ID：{user_id}，原因：未提供要更新的字段")
            raise HTTPException(status_code=400, detail="请提供要更新的字段")

        # 调用CRUD更新用户
        user, msg = await UserCRUD.update_user(db, user_id, **update_kwargs)

        if not user:
            api_logger.warning(f"更新用户失败 - 用户ID：{user_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"更新用户成功 - 用户ID：{user_id}，更新后用户名：{user.username}")
        return ResponseModel(
            code=200,
            message=msg,
            data=UserResponse.from_orm(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"更新用户异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新用户时发生服务器内部错误")


# 6. 删除用户
@router.delete(
    "/{user_id}",
    response_model=ResponseModel,
    summary="删除用户",
    description="根据用户ID删除用户（物理删除）"
)
async def delete_user(
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除用户请求 - 用户ID：{user_id}（物理删除）")
    try:
        is_del, msg = await UserCRUD.delete_user(db, user_id)

        if not is_del:
            api_logger.error(f"删除用户失败 - 用户ID：{user_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除用户成功 - 用户ID：{user_id}")
        return ResponseModel(
            code=200,
            message=msg,
            data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.critical(f"删除用户异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除用户时发生服务器内部错误")
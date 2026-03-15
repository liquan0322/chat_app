from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

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
    # 加密密码
    hashed_password = get_password_hash(user_in.password)

    # 调用CRUD创建用户
    user, msg = await UserCRUD.create_user(
        db=db,
        username=user_in.username,
        hashed_password=hashed_password,
        email=user_in.email
    )

    if not user:
        raise HTTPException(status_code=400, detail=msg)

    return ResponseModel(
        code=200,
        message=msg,
        data=UserResponse.from_orm(user)
    )


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
    user = await UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ResponseModel(
        code=200,
        message="查询成功",
        data=UserResponse.from_orm(user)
    )


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
    user = await UserCRUD.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ResponseModel(
        code=200,
        message="查询成功",
        data=UserResponse.from_orm(user)
    )


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
    users = await UserCRUD.get_all_users(db, skip=skip, limit=limit)

    # 转换为响应模型列表
    user_list = [UserResponse.from_orm(user) for user in users]

    return ResponseModel(
        code=200,
        message="查询成功",
        data=user_list
    )


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
    # 构造更新参数（过滤空值）
    update_kwargs = {}
    if user_in.username:
        update_kwargs["username"] = user_in.username
    if user_in.email:
        update_kwargs["email"] = user_in.email
    if user_in.password:
        update_kwargs["hashed_password"] = get_password_hash(user_in.password)

    if not update_kwargs:
        raise HTTPException(status_code=400, detail="请提供要更新的字段")

    # 调用CRUD更新用户
    user, msg = await UserCRUD.update_user(db, user_id, **update_kwargs)

    if not user:
        raise HTTPException(status_code=400, detail=msg)

    return ResponseModel(
        code=200,
        message=msg,
        data=UserResponse.from_orm(user)
    )


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
    is_del, msg = await UserCRUD.delete_user(db, user_id)

    if not is_del:
        raise HTTPException(status_code=400, detail=msg)

    return ResponseModel(
        code=200,
        message=msg,
        data=True
    )
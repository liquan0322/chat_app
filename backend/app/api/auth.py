from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel
import asyncio

from app.core.jwt_utils import (
    verify_password_async, get_password_hash_async,
    create_access_token, create_refresh_token,
    get_current_user_async, verify_token_async
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 模拟异步用户数据库（实际项目用异步ORM如SQLAlchemy 2.0/AsyncPG）
fake_users_db = {}


# 注册请求模型
class RegisterRequest(BaseModel):
    username: str
    password: str


# -------------------------- 异步接口实现 --------------------------
@router.post("/register")
async def register_async(user: RegisterRequest):
    """异步注册接口"""
    # 模拟异步查询用户是否存在
    await asyncio.sleep(0.01)
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 异步生成密码哈希
    hashed_password = await get_password_hash_async(user.password)

    # 模拟异步存储用户
    user_id = str(len(fake_users_db) + 1)
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "user_id": user_id
    }

    return {"message": "注册成功", "username": user.username, "user_id": user_id}


@router.post("/login")
async def login_async(form_data: OAuth2PasswordRequestForm = Depends()):
    """异步登录接口（返回JWT Token）"""
    # 模拟异步查询用户
    await asyncio.sleep(0.01)
    user = fake_users_db.get(form_data.username)

    # 异步验证密码
    if not user or not await verify_password_async(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成Token（同步操作，不阻塞）
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["user_id"], "username": user["username"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user["user_id"], "username": user["username"]}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "username": user["username"]
    }


@router.post("/refresh-token")
async def refresh_token_async(refresh_token: str):
    """异步刷新Token接口"""
    # 异步验证刷新Token
    payload = await verify_token_async(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新Token"
        )

    # 生成新的访问Token
    new_access_token = create_access_token(
        data={"sub": payload["sub"], "username": payload["username"]}
    )
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me_async(current_user: dict = Depends(get_current_user_async)):
    """异步获取当前用户信息（受保护接口）"""
    return current_user
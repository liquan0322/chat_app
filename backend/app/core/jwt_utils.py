from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import asyncio  # 模拟异步数据库操作

# 配置项（生产环境建议用.env文件）
SECRET_KEY = "your-strong-secret-key-32bytes-long-1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2令牌载体
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# -------------------------- 异步工具函数 --------------------------
async def verify_password_async(plain_password: str, hashed_password: str):
    """异步验证密码（模拟异步IO）"""
    # 实际项目中可替换为异步数据库查询/缓存查询
    await asyncio.sleep(0.01)
    return pwd_context.verify(plain_password, hashed_password)


async def get_password_hash_async(password: str):
    """异步生成密码哈希（模拟异步IO）"""
    await asyncio.sleep(0.01)
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """生成访问Token（CPU操作，无需异步）"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    """生成刷新Token（CPU操作，无需异步）"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_token_async(token: str):
    """异步校验Token（封装同步操作，避免阻塞事件循环）"""
    try:
        # 用asyncio.to_thread将同步JWT解码放到线程池，不阻塞异步事件循环
        payload = await asyncio.to_thread(
            jwt.decode, token, SECRET_KEY, algorithms=[ALGORITHM]
        )

        # 验证Token类型
        token_type = payload.get("type")
        if token_type not in ["access", "refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token类型"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期或无效",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_async(token: str = Depends(oauth2_scheme)):
    """异步获取当前用户（接口依赖项）"""
    payload = await verify_token_async(token)
    user_id: str = payload.get("sub")
    username: str = payload.get("username")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证用户信息"
        )

    # 模拟异步查询用户信息（实际项目中替换为异步数据库查询）
    await asyncio.sleep(0.01)
    return {"user_id": user_id, "username": username}
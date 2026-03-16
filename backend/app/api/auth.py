from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
# 导入 JWT 工具类、数据库会话、User 模型
from app.core.jwt_auth import AsyncJWTAuth, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.session import get_async_db
from app.models.user import User
# 导入日志实例
from app.core.logging import auth_logger

# 创建路由实例
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# OAuth2 密码模式依赖（token 接口地址）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# 类型注解别名（简化代码）
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

# ------------------------------
# 通用依赖：获取当前登录用户
# ------------------------------
async def get_current_user(
        token: TokenDep,
        db: AsyncSessionDep
):
    """通用依赖：验证token并返回当前用户"""
    try:
        user = await AsyncJWTAuth.get_current_user(db, token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except ValueError as e:
        auth_logger.warning(f"用户认证失败: {str(e)} | token: {token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ------------------------------
# 认证相关接口
# ------------------------------
@router.post("/token", summary="用户登录获取令牌", status_code=status.HTTP_200_OK)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: AsyncSessionDep
):
    """
    用户登录接口（OAuth2 密码模式）
    - form_data: 包含 username/password 的表单数据
    - 返回 access_token/refresh_token
    """
    # 记录登录尝试
    auth_logger.info(f"用户登录尝试 | 用户名: {form_data.username}")

    # 验证用户名密码
    user = await AsyncJWTAuth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        auth_logger.warning(f"登录失败 | 用户名: {form_data.username} | 原因: 用户名或密码错误")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成令牌
    access_token = AsyncJWTAuth.create_access_token(user_id=user.id)
    refresh_token = AsyncJWTAuth.create_refresh_token(user_id=user.id)

    # 记录登录成功
    auth_logger.info(f"登录成功 | 用户ID: {user.id} | 用户名: {user.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@router.post("/refresh", summary="刷新访问令牌", status_code=status.HTTP_200_OK)
async def refresh_access_token(
        refresh_token: Annotated[str, Body(..., embed=True, description="刷新令牌")],
        db: AsyncSessionDep
):
    """
    使用 refresh_token 刷新 access_token
    - refresh_token: 刷新令牌
    - 返回新的 access_token
    """
    try:
        # 验证 refresh_token 并获取用户
        user = await AsyncJWTAuth.get_current_user(db, refresh_token)
        # 生成新的 access_token
        new_access_token = AsyncJWTAuth.create_access_token(user_id=user.id)

        auth_logger.info(f"令牌刷新成功 | 用户ID: {user.id}")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except ValueError as e:
        auth_logger.warning(f"令牌刷新失败 | 原因: {str(e)} | refresh_token: {refresh_token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", summary="获取当前登录用户信息", status_code=status.HTTP_200_OK)
async def get_current_user_info(
        current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取当前登录用户的基本信息（需携带有效 access_token）
    """
    auth_logger.info(f"获取用户信息 | 用户ID: {current_user.id}")

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }
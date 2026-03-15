# app/core/jwt_auth.py
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# 导入你的 User 模型
from app.models.user import User

# ------------------------------
# 配置项（建议最终移到 app/core/config.py 中）
# ------------------------------
SECRET_KEY = "your-strong-secret-key-here-keep-it-safe"  # 生产环境务必更换
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌过期时间
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 刷新令牌过期时间

# 密码加密上下文（与 User 表的 hashed_password 对应）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ------------------------------
# 核心 JWT 工具类（异步）
# ------------------------------
class AsyncJWTAuth:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与加密密码是否匹配"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """生成密码的加密哈希值"""
        return pwd_context.hash(password)

    @staticmethod
    def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """生成 JWT Token（同步，无 IO 操作）"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_access_token(cls, user_id: int) -> str:
        """生成访问令牌"""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return cls.create_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """生成刷新令牌"""
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        return cls.create_token(
            data={"sub": str(user_id), "type": "refresh"},
            expires_delta=refresh_token_expires
        )

    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
        """异步验证 Token 并获取当前用户"""
        credentials_exception = ValueError("Could not validate credentials")

        try:
            # 解析 Token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception

            # 异步查询用户
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user = result.scalars().first()

            if user is None:
                raise credentials_exception
            return user

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise credentials_exception
        except Exception as e:
            raise ValueError(f"Authentication error: {str(e)}")

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """异步验证用户凭据（用户名+密码）"""
        # 异步查询用户
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if not user or not AsyncJWTAuth.verify_password(password, user.hashed_password):
            return None
        return user
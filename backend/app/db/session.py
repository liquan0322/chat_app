from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import AppSettings

settings = AppSettings()
async_database_url = settings.db_url

# 创建异步数据库引擎
async_engine = create_async_engine(
    async_database_url,
    echo=settings.sqlalchemy_echo, # 从环境变量控制是否打印 SQL
    pool_pre_ping=True,            # 检查连接有效性
    pool_size=settings.sqlalchemy_pool_size,
    max_overflow=settings.sqlalchemy_max_overflow,
)


# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,  # 指定为异步会话
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # 提交后不自动过期对象
)


# ------------------------------
# 异步数据库会话生成器（核心）
# ------------------------------
async def get_async_db():
    """
    异步获取数据库会话（替代同步的get_db）
    用法：async for db in get_async_db(): ...
    """
    # 创建异步会话实例
    db = AsyncSessionLocal()
    try:
        yield db  # 异步生成器返回会话
    finally:
        # 确保会话关闭（异步关闭）
        await db.close()
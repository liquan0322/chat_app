# app/db/session.py (异步版本)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ------------------------------
# 异步数据库配置
# PostgreSQL: asyncpg (推荐) → postgresql+asyncpg://user:password@host:port/dbname

ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:123456@postgres:5432/postgres"

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # 生产环境关闭echo，调试时可打开
    pool_pre_ping=True,  # 连接池预检查，避免无效连接
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
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
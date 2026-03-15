"""
FastAPI 异步项目入口文件
核心改造：全异步化 + 规范项目结构 + 修复异步建表问题
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# 项目内部模块导入
from app.api import (
    auth, individual_conversations, group_conversations, users, robots
)
from app.db.session import get_async_db, async_engine
from app.db.base import Base
import app.models  # 确保所有模型被导入，以便建表

# ------------------------------
# 1. 异步建表核心逻辑（关键修复）
# ------------------------------
async def init_database():
    """
    异步初始化数据库：创建所有表
    替代同步的 Base.metadata.create_all(bind=async_engine)
    """
    try:
        async with async_engine.begin() as conn:
            # 异步执行同步建表逻辑（AsyncEngine 专属方法）
            await conn.run_sync(Base.metadata.create_all)
        print("数据库表异步创建完成")
    except Exception as e:
        print(f"数据库初始化失败：{str(e)}")
        raise  # 建表失败则终止服务启动

# ------------------------------
# 2. FastAPI 应用实例化（异步配置）
# ------------------------------
app = FastAPI(
    title="chat_app",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    description="Chat App 异步API服务（FastAPI + 异步SQLAlchemy）"
)

# ------------------------------
# 3. 中间件配置（异步兼容）
# ------------------------------
# CORS 配置（放开跨域，适配前端联调）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境放开所有，生产环境替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# 4. 启动/关闭事件（异步生命周期）
# ------------------------------
@app.on_event("startup")
async def startup_event():
    """FastAPI启动时执行的异步初始化操作"""
    # 1. 初始化数据库表
    await init_database()
    # 2. 可添加其他异步初始化逻辑（如缓存、消息队列连接）
    print("🚀 Chat App API 服务启动成功")

@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI关闭时执行的异步清理操作"""
    # 关闭异步数据库引擎连接池
    await async_engine.dispose()
    print("🛑 Chat App API 服务已关闭，数据库连接已释放")

# ------------------------------
# 5. 路由注册（异步接口）
# ------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(robots.router)
app.include_router(individual_conversations.router)
app.include_router(group_conversations.router)

# ------------------------------
# 6. 基础接口（异步兼容）
# ------------------------------
@app.get("/health", tags=["健康检查"])
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """异步健康检查接口：验证数据库连接"""
    try:
        # 异步执行SQL查询（必须加 await）
        result = await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据库连接失败：{str(e)}"
        )

@app.get("/", tags=["根路由"])
async def root():
    """根路由（改为异步，保持一致性）"""
    return {
        "message": "Welcome to Chat App API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# ------------------------------
# 7. 本地启动入口（异步兼容）
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    # 开发环境启动配置（热重载 + 异步）
    uvicorn.run(
        "main:app",  # 注意：这里必须是字符串 "main:app"，而非直接传 app 实例
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境热重载，生产环境禁用
        log_level="info"
    )








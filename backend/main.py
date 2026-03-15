"""
FastAPI 异步项目入口文件
核心改造：全异步化 + 规范项目结构 + 修复异步建表问题 + 集成结构化日志
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import sys

# ========== 核心：导入自定义日志配置 ==========
# 请确保日志配置文件路径正确（根据你的项目结构调整）
from app.core.logging import logger, db_logger, api_logger

# 项目内部模块导入
from app.api import (
    auth, individual_conversations, group_conversations, users, robots
)
from app.db.session import get_async_db, async_engine
from app.db.base import Base
import app.models  # 确保所有模型被导入，以便建表


# ------------------------------
# 1. 异步建表核心逻辑（关键修复 + 日志增强）
# ------------------------------
async def init_database():
    """
    异步初始化数据库：创建所有表
    替代同步的 Base.metadata.create_all(bind=async_engine)
    """
    # 记录初始化开始（DEBUG级别，开发环境可见）
    db_logger.debug("开始异步初始化数据库表结构")
    try:
        async with async_engine.begin() as conn:
            # 异步执行同步建表逻辑（AsyncEngine 专属方法）
            await conn.run_sync(Base.metadata.create_all)
        # 记录成功（INFO级别，生产环境可见）
        db_logger.info("✅ 数据库表异步创建完成")
    except Exception as e:
        # 记录错误（ERROR级别，附带完整堆栈信息）
        db_logger.error(f"❌ 数据库初始化失败：{str(e)}", exc_info=True)
        raise  # 建表失败则终止服务启动


# ------------------------------
# 2. FastAPI 应用实例化（异步配置）
# ------------------------------
app = FastAPI(
    title="chat_app",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    description="Chat App 异步API服务（FastAPI + 异步SQLAlchemy + 结构化日志）"
)

# ------------------------------
# 3. 中间件配置（异步兼容）
# ------------------------------
# CORS 配置（放开跨域，适配前端联调）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境替换为具体域名，如 ["https://chat.example.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------
# 4. 启动/关闭事件（异步生命周期 + 日志）
# ------------------------------
@app.on_event("startup")
async def startup_event():
    """FastAPI启动时执行的异步初始化操作"""
    logger.info("🚀 开始启动 Chat App API 服务")
    try:
        # 1. 初始化数据库表
        await init_database()
        # 2. 记录路由注册信息
        api_logger.info(f"已注册路由数：{len(app.routes)}")
        logger.info("✅ Chat App API 服务启动成功")
    except Exception as e:
        logger.critical(f"💥 服务启动失败：{str(e)}", exc_info=True)
        sys.exit(1)  # 启动失败直接退出进程


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI关闭时执行的异步清理操作"""
    logger.info("🛑 开始关闭 Chat App API 服务")
    try:
        # 关闭异步数据库引擎连接池
        await async_engine.dispose()
        db_logger.info("数据库连接池已释放")
        logger.info("✅ Chat App API 服务已正常关闭")
    except Exception as e:
        logger.error(f"⚠️ 服务关闭时发生异常：{str(e)}", exc_info=True)


# ------------------------------
# 5. 路由注册（异步接口）
# ------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(robots.router)
app.include_router(individual_conversations.router)
app.include_router(group_conversations.router)


# ------------------------------
# 6. 基础接口（异步兼容 + 日志）
# ------------------------------
@app.get("/health", tags=["健康检查"])
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """异步健康检查接口：验证数据库连接"""
    api_logger.debug("接收到健康检查请求，开始验证数据库连接")
    try:
        # 异步执行SQL查询（必须加 await）
        result = await db.execute(text("SELECT 1"))
        db_result = result.scalar()

        if db_result == 1:
            api_logger.info("健康检查通过：数据库连接正常")
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": asyncio.get_event_loop().time(),
                "service": "chat_app_api"
            }
        else:
            api_logger.warning("健康检查失败：数据库查询结果异常")
            raise HTTPException(status_code=500, detail="数据库查询结果异常")
    except Exception as e:
        api_logger.error(f"健康检查失败：数据库连接异常 - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"数据库连接失败：{str(e)}"
        )


@app.get("/", tags=["根路由"])
async def root():
    """根路由（改为异步，保持一致性）"""
    api_logger.debug("访问根路由")
    return {
        "message": "Welcome to Chat App API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0"
    }


# ------------------------------
# 7. 本地启动入口（异步兼容）
# ------------------------------
if __name__ == "__main__":
    import uvicorn

    # 记录启动参数
    logger.info("📢 本地启动 Chat App API 服务（开发环境）")
    # 开发环境启动配置（热重载 + 异步）
    uvicorn.run(
        "main:app",  # 注意：这里必须是字符串 "main:app"，而非直接传 app 实例
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境热重载，生产环境禁用
        log_level="info"  # uvicorn 基础日志级别（自定义日志已独立配置）
    )
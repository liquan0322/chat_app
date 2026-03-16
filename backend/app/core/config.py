from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# 定义配置模型
class AppSettings(BaseSettings):
    # -------------------------- 模型配置 --------------------------
    # 配置 .env 文件路径和编码
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量名不区分大小写
        extra="ignore"  # 忽略未定义的环境变量
    )

    # -------------------------- 数据库核心配置 --------------------------
    db_user: str
    db_password: str
    db_server: str
    db_port: int
    db_name: str
    #
    # # -------------------------- SQLAlchemy 配置 --------------------------
    sqlalchemy_echo: bool
    sqlalchemy_pool_size: int
    sqlalchemy_max_overflow: int


    # -------------------------- 辅助方法 --------------------------
    @property
    def db_url(self):
        """生成 SQLAlchemy 可用的数据库连接 URL"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_server}:{self.db_port}/{self.db_name}"
        )



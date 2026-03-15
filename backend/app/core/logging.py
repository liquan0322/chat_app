import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

# ===================== 基础配置 =====================
# 项目根目录
BASE_DIR = Path(__file__).parent.parent
# 日志目录（自动创建）
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志级别映射
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 默认日志级别（生产环境建议INFO，开发环境DEBUG）
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ===================== 日志格式 =====================
# 详细格式（文件日志）
DETAILED_FORMAT = logging.Formatter(
    "%(asctime)s - %(name)s - %(process)d:%(thread)d - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 简单格式（控制台日志）
SIMPLE_FORMAT = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# ===================== 配置函数 =====================
def setup_logger(name: str = "chat_app") -> logging.Logger:
    """
    配置标准Logger
    :param name: Logger名称
    :return: 配置好的Logger实例
    """
    # 创建Logger（避免重复配置）
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 已配置过，直接返回

    # 设置基础级别
    logger.setLevel(LOG_LEVEL_MAP.get(DEFAULT_LOG_LEVEL, logging.INFO))
    logger.propagate = False  # 禁止向上传播，避免重复输出

    # 1. 控制台处理器（输出INFO及以上级别）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SIMPLE_FORMAT)
    logger.addHandler(console_handler)

    # 2. 通用文件处理器（所有级别，按大小轮转）
    file_handler = RotatingFileHandler(
        filename=LOG_DIR / "chat_app.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,  # 保留10个备份文件
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(file_handler)

    # 3. 错误日志处理器（仅ERROR/CRITICAL级别，单独存储）
    error_file_handler = RotatingFileHandler(
        filename=LOG_DIR / "chat_app_error.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(error_file_handler)

    return logger


# ===================== 全局Logger实例 =====================
# 项目主Logger
logger = setup_logger("chat_app")

# 按模块拆分的Logger（可选，便于分类排查）
auth_logger = setup_logger("chat_app.auth")  # 认证模块
api_logger = setup_logger("chat_app.api")  # API模块
db_logger = setup_logger("chat_app.db")  # 数据库模块
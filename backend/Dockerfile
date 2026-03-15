# 构建阶段
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（PostgreSQL 客户端、编译依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到虚拟环境（减少镜像体积）
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim AS runner

# 创建appuser并赋予/app目录权限（关键修复！）
RUN useradd -m appuser \
    && mkdir -p /app \
    && chown -R appuser:appuser /app  # 赋予用户对/app目录的完整权限

# 切换到非root用户
USER appuser

# 设置工作目录（固化，确保gunicorn基于此目录解析模块）
WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码（切换用户后复制，确保文件归属正确）
COPY --chown=appuser:appuser . .

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# 新增：强制Python以/app为根目录解析模块（关键！）
ENV PYTHONPATH="/app:${PYTHONPATH}"

# 先验证模块是否可导入（提前暴露问题，便于调试）
RUN python -c "import app.main; print('模块导入成功')" || echo "模块导入失败，请检查路径"

# 启动命令（优化参数顺序，保持兼容性）
CMD ["gunicorn", "--chdir", "/app", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000"]
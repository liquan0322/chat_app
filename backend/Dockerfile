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

# 设置非root用户（提升安全性）
RUN useradd -m appuser
USER appuser

# 设置工作目录
WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
# 实时输出日志
ENV PYTHONUNBUFFERED=1
# 不生成pyc文件
ENV PYTHONDONTWRITEBYTECODE=1

# 启动命令（生产环境使用gunicorn）
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000"]
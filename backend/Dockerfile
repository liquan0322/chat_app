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
COPY . .

# 安装依赖到虚拟环境（减少镜像体积）
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim AS runner

# 创建appuser并赋予/app目录权限
#RUN useradd -m appuser \
#    && mkdir -p /app \
#    && chown -R appuser:appuser /app

# 切换到非root用户
#USER appuser

# 设置工作目录
WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码
#COPY --chown=appuser:appuser . .


# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 核心修改：直接用uvicorn启动（生产环境配置多进程）
# 注意：把「app.main:app」换成你实际能启动的uvicorn命令中的路径（比如main:app）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
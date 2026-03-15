#!/bin/bash

# 复制环境变量示例文件（若不存在）
if [ ! -f .env ]; then
    cp .env.example .env
    echo "已创建 .env 文件，请编辑后重新运行本脚本！"
    exit 1
fi

# 停止之前服务
docker-compose down -v
# 启动所有服务
docker-compose up -d

# 等待数据库就绪
echo "等待数据库初始化..."
sleep 10

# 初始化数据库（迁移+预设机器人）
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.init_robots

echo "所有服务启动完成！"
#echo "前端访问地址：http://81.70.181.67:$(grep FRONTEND_PORT .env | cut -d'=' -f2)"
echo "后端 API 文档：http://81.70.181.67:$(grep BACKEND_PORT .env | cut -d'=' -f2)/docs"
echo "数据库地址：http://81.70.181.67:$(grep DB_PORT .env | cut -d'=' -f2)（用户：$(grep DB_USER .env | cut -d'=' -f2)）"
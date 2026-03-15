# 构建阶段
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件（利用缓存，修改代码不重新安装依赖）
COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com  # 国内源加速

# 复制前端代码
COPY . .

# 构建生产包
RUN npm run build

# 运行阶段（Nginx 轻量镜像）
FROM nginx:1.25-alpine AS runner

# 复制构建产物到 Nginx 静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置（解决前端路由刷新 404 问题）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
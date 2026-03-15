# 构建阶段
FROM node:18-alpine AS builder

# 安装依赖（解决 alpine 缺少构建工具的问题，如 node-gyp）
RUN apk add --no-cache git

# 设置工作目录
WORKDIR /app

# 配置 npm 国内源（全局生效，避免后续安装依赖走默认源）
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件（利用缓存层，仅当 package.json 变化时重新安装）
COPY package.json package-lock.json ./

# 严格安装依赖（ci 模式比 install 更严格，匹配 package-lock.json）
RUN npm ci

# 复制所有前端代码（排除 .dockerignore 中的文件）
COPY . .

# 打印目录结构（调试用，确认 src/views/Auth.vue 存在）
RUN ls -la src/views/

# 构建生产包（若构建失败，会输出详细错误）
RUN npm run build

# 运行阶段（轻量 Nginx）
FROM nginx:1.25-alpine AS runner

# 移除默认 Nginx 配置（避免冲突）
RUN rm -rf /etc/nginx/conf.d/default.conf

# 复制构建产物到 Nginx 静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置（解决前端路由刷新 404）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx（前台运行）
CMD ["nginx", "-g", "daemon off;"]
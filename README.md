# chat_app
在线聊天应用前后端实现方案
基于 FastAPI 实现后端服务，包含用户认证、个人对话、群组对话等核心功能，并提供前端简易实现、测试用例和部署说明。
目前仅实现了docker部署、FastAPI后端主要接口以及测试代码，前端页面时间和技术熟悉度问题未能实现。

一、技术选型与版本

组件	      技术栈	         版本	      选择理由
后端框架	  FastAPI	     0.104.1	  高性能、自动生成 API 文档、类型提示、异步支持，适合构建现代化 API
编程语言	  Python	     3.11	      生态丰富、语法简洁，异步支持完善
数据库	  PostgreSQL	 15	          强大的关系型数据库，支持 JSON 类型（适合存储标签）、事务、索引优化
ORM	      SQLAlchemy	 2.0	      成熟的 ORM 框架，支持异步操作，类型安全
认证	      JWT (PyJWT)	 2.8.0	      无状态认证，适合前后端分离架构
前端	      Vue 3 + Vite	 4.4	      轻量、快速，易于实现简单交互界面
测试	      Pytest	     7.4	      Python 主流测试框架，支持异步测试


二、核心设计考量
    1.数据隔离：所有数据库查询都强制带上用户 ID 过滤，确保用户只能访问自己的数据
    2.AI 调用健壮性：实现重试机制 + 失败降级 + 数据一致性保障
    3.群组机器人逻辑：基于 "人类消息触发" 机制防止循环，策略化机器人响应规则
    4.标签系统：采用多对多关系设计，支持高效筛选和管理
    5.API 设计：严格遵循 RESTful 规范，提供完整的错误处理和状态码

三、数据库设计
3.1 核心表结构（PostgreSQL）
sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 机器人角色表
CREATE TABLE bot_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 角色名称：客服机器人、技术机器人等
    personality TEXT NOT NULL,         -- 性格描述
    response_template TEXT NOT NULL    -- 回复模板
);

-- 个人对话表
CREATE TABLE individual_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 对话标签表
CREATE TABLE conversation_tags (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    tag_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES individual_conversations(id) ON DELETE CASCADE,
    UNIQUE(conversation_id, tag_name)  -- 避免重复标签
);

-- 个人消息表
CREATE TABLE individual_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_type VARCHAR(20) NOT NULL,  -- 'user' 或 'ai'
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'success',  -- success/failed/retrying
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES individual_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 群组对话表
CREATE TABLE group_conversations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    creator_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_human_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 防机器人循环
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- 群组成员表（用户）
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES group_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(group_id, user_id)
);

-- 群组机器人表
CREATE TABLE group_bots (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    bot_role_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES group_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (bot_role_id) REFERENCES bot_roles(id),
    UNIQUE(group_id, bot_role_id)
);

-- 群组消息表
CREATE TABLE group_messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    sender_type VARCHAR(20) NOT NULL,  -- 'user' 或 'bot'
    sender_id INTEGER NOT NULL,  -- 用户ID或机器人角色ID
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_triggered_response BOOLEAN DEFAULT FALSE,  -- 是否是触发式回复
    FOREIGN KEY (group_id) REFERENCES group_conversations(id) ON DELETE CASCADE
);

-- 索引优化
CREATE INDEX idx_individual_conversations_user_id ON individual_conversations(user_id);
CREATE INDEX idx_conversation_tags_tag_name ON conversation_tags(tag_name);
CREATE INDEX idx_individual_messages_conversation_id ON individual_messages(conversation_id);
CREATE INDEX idx_group_conversations_creator_id ON group_conversations(creator_id);
CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_bots_group_id ON group_bots(group_id);
CREATE INDEX idx_group_messages_group_id ON group_messages(group_id);
CREATE INDEX idx_group_messages_created_at ON group_messages(created_at);
2.2 设计考量
标签存储：采用单独的 conversation_tags 表，支持多标签，通过唯一约束避免重复，便于按标签筛选
权限隔离：所有表都通过外键关联到用户 ID，确保只能访问自己的数据
群组防循环：通过 last_human_message_at 字段记录最后人类消息时间，机器人仅在有新人类消息时回复
消息状态：个人消息表增加 status 字段，记录 AI 调用状态，保障数据一致性
索引设计：为常用查询字段创建索引，优化标签筛选、消息查询等性能


三、后端实现
3.1 项目结构
|-- LICENSE
|-- README.md
|-- backend
|   |-- Dockerfile
|   |-- alembic
|   |   |-- __init__.py
|   |   `-- env.py
|   |-- app
|   |   |-- api
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- group_conversations.py
|   |   |   |-- individual_conversations.py
|   |   |   |-- robots.py
|   |   |   `-- users.py
|   |   |-- core
|   |   |   |-- __init__.py
|   |   |   |-- config.py
|   |   |   |-- jwt_auth.py
|   |   |   |-- logging.py
|   |   |   `-- security.py
|   |   |-- crud
|   |   |   |-- __init__.py
|   |   |   |-- group_conversation.py
|   |   |   |-- individual_conversation.py
|   |   |   |-- robot.py
|   |   |   `-- user.py
|   |   |-- db
|   |   |   |-- __init__.py
|   |   |   |-- base.py
|   |   |   `-- session.py
|   |   |-- logs
|   |   |   |-- chat_app.log
|   |   |   `-- chat_app_error.log
|   |   |-- models
|   |   |   |-- __init__.py
|   |   |   |-- group_conversation.py
|   |   |   |-- individual_conversation.py
|   |   |   |-- robot.py
|   |   |   `-- user.py
|   |   |-- schemas
|   |   |   |-- __init__.py
|   |   |   |-- group_conversation.py
|   |   |   |-- individual_conversation.py
|   |   |   |-- robot.py
|   |   |   `-- user.py
|   |   `-- services
|   |       |-- __init__.py
|   |       `-- ai_client.py
|   |-- main.py
|   `-- requirements.txt
|-- docker-compose.yml
`-- start.sh
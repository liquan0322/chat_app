# chat_app
在线聊天应用前后端实现方案

		基于 FastAPI 实现后端服务，包含用户认证、个人对话、群组对话等核心功能，并提供前端简易实现、测试用例和部署说明。

		目前仅实现了docker部署、FastAPI后端主要接口以及测试代码，前端页面时间和技术熟悉度问题未能实现，抱歉。

		后端服务云部署IP地址为：http://81.70.181.67:8000
		
		后端服务 Swgger UI IP地址为：http://81.70.181.67:8000/docs#/




一、技术选型与版本

		1.后端框架：FastAPI=0.104.1，选择理由：高性能、自动生成 API 文档、类型提示、异步支持，适合构建现代化 API

		2.编程语言：Python=3.11，选择理由：生态丰富、语法简洁，异步支持完善

		3.数据库：PostgreSQL=15，选择理由：强大的关系型数据库，支持 JSON 类型（适合存储标签）、事务、索引优化

		4.ORM：SQLAlchemy=2.0，选择理由：成熟的 ORM 框架，支持异步操作，类型安全

		5.认证：JWT (PyJWT)=2.8.0，选择理由：无状态认证，适合前后端分离架构

		6.前端：Vue 3 + Vite=4.4，选择理由：轻量、快速，易于实现简单交互界面

		7.测试：Pytest=7.4，选择理由：Python 主流测试框架，支持异步测试


二、核心设计考量

		1.数据隔离：所有数据库查询都强制带上用户 ID 过滤，确保用户只能访问自己的数据
    
		2.AI 调用健壮性：实现重试机制 + 失败降级 + 数据一致性保障
    
		3.群组机器人逻辑：基于 "人类消息触发" 机制防止循环，策略化机器人响应规则
    
		4.标签系统：采用多对多关系设计，支持高效筛选和管理
    
		5.API 设计：严格遵循 RESTful 规范，提供完整的错误处理和状态码

三、数据库设计
3.1 核心表结构（PostgreSQL ORM）



-- 用户表
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    individual_conversations = relationship("IndividualConversation", back_populates="user",
                                            cascade="all, delete-orphan")
    conversation_tags = relationship("ConversationTag", back_populates="user", cascade="all, delete-orphan")
    individual_messages = relationship("IndividualMessage", back_populates="user", cascade="all, delete-orphan")
    created_groups = relationship("GroupConversation", back_populates="creator",
                                  foreign_keys="GroupConversation.creator_id")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="sender", foreign_keys="GroupMessage.sender_id")





-- 机器人角色表
class AiRobot(Base):
    __tablename__ = "ai_robots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)  # 客服、技术、幽默等
    personality = Column(Text, nullable=True)  # 性格描述
    response_template = Column(Text, nullable=True)  # 回复模板
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    group_robots = relationship("GroupRobot", back_populates="robot", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="robot", foreign_keys="GroupMessage.robot_id")


-- 个人对话表
class IndividualConversation(Base):
    __tablename__ = "individual_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    user = relationship("User", back_populates="individual_conversations")
    conversation_tags = relationship("ConversationTag", back_populates="conversation", cascade="all, delete-orphan")
    individual_messages = relationship("IndividualMessage", back_populates="conversation", cascade="all, delete-orphan")


-- 对话标签表
class ConversationTag(Base):
    __tablename__ = "conversation_tags"
    __table_args__ = (
        UniqueConstraint("conversation_id", "tag", name="uq_conversation_tag"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("individual_conversations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    conversation = relationship("IndividualConversation", back_populates="conversation_tags")
    user = relationship("User", back_populates="conversation_tags")


-- 个人消息表
class IndividualMessage(Base):
    __tablename__ = "individual_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("individual_conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    is_user_message = Column(Boolean, nullable=False)
    ai_error = Column(Text, nullable=True)  # 存储AI调用错误信息
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    conversation = relationship("IndividualConversation", back_populates="individual_messages")
    user = relationship("User", back_populates="individual_messages")


-- 群组对话表
class GroupConversation(Base):
    __tablename__ = "group_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 关联关系
    creator = relationship("User", back_populates="created_groups")
    group_members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    group_robots = relationship("GroupRobot", back_populates="group", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan")
    conversation_state = relationship("GroupConversationState", back_populates="group", uselist=False,
                                      cascade="all, delete-orphan")


-- 群组成员表（用户）
class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_members")
    user = relationship("User", back_populates="group_memberships")


-- 群组机器人表
class GroupRobot(Base):
    __tablename__ = "group_robots"
    __table_args__ = (
        UniqueConstraint("group_id", "robot_id", name="uq_group_robot"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    robot_id = Column(Integer, ForeignKey("ai_robots.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), default=func.current_timestamp())

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_robots")
    robot = relationship("AiRobot", back_populates="group_robots")


-- 群组消息表
class GroupMessage(Base):
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL表示机器人
    robot_id = Column(Integer, ForeignKey("ai_robots.id"), nullable=True)  # NULL表示人类用户
    message = Column(Text, nullable=False)
    is_human = Column(Boolean, nullable=False)  # 是否人类发送
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    reply_to_message_id = Column(Integer, ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)

    # 关联关系
    group = relationship("GroupConversation", back_populates="group_messages")
    sender = relationship("User", back_populates="group_messages", foreign_keys=[sender_id])
    robot = relationship("AiRobot", back_populates="group_messages", foreign_keys=[robot_id])
    replied_message = relationship("GroupMessage", remote_side=[id], backref="replies")


-- 索引优化

    CREATE INDEX idx_individual_conversations_user_id ON individual_conversations(user_id);
	
    CREATE INDEX idx_conversation_tags_tag_name ON conversation_tags(tag_name);
	
    CREATE INDEX idx_individual_messages_conversation_id ON individual_messages(conversation_id);
	
    CREATE INDEX idx_group_conversations_creator_id ON group_conversations(creator_id);
	
    CREATE INDEX idx_group_members_group_id ON group_members(group_id);
	
    CREATE INDEX idx_group_bots_group_id ON group_bots(group_id);
	
    CREATE INDEX idx_group_messages_group_id ON group_messages(group_id);
	
    CREATE INDEX idx_group_messages_created_at ON group_messages(created_at);
	
3.2 设计考量

	标签存储：采用单独的 conversation_tags 表，支持多标签，通过唯一约束避免重复，便于按标签筛选

	权限隔离：所有表都通过外键关联到用户 ID，确保只能访问自己的数据

	索引设计：为常用查询字段创建索引，优化标签筛选、消息查询等性能





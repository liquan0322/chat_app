# 导入基础依赖（新增异步相关）
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器
# 导入项目已封装的异步数据库工具和用户模型（需确保项目有异步版本）
from app.db.session import get_async_db  # 替换为异步数据库会话生成器
from app.models.user import User

# ========== 核心：导入日志实例 ==========
from app.core.logging import db_logger, logger


# 用户CRUD操作类（全异步 + 日志集成）
class UserCRUD:
    @staticmethod
    async def create_user(db, username, hashed_password, email):
        """
        异步创建新用户
        :param db: 异步数据库会话（AsyncSession）
        :param username: 用户名
        :param hashed_password: 加密后的密码（禁止传明文）
        :param email: 邮箱
        :return: (用户对象/None, 提示信息)
        """
        # 记录创建用户请求（DEBUG级别，开发环境可见）
        db_logger.debug(f"开始异步创建用户 - 用户名：{username}，邮箱：{email}")
        try:
            # 构建用户对象
            user = User(
                username=username,
                hashed_password=hashed_password,
                email=email
            )
            db.add(user)
            await db.commit()  # 异步提交
            await db.refresh(user)  # 异步刷新获取自动生成字段

            # 记录创建成功（INFO级别，生产环境可见）
            db_logger.info(f"用户创建成功 - 用户ID：{user.id}，用户名：{user.username}，邮箱：{user.email}")
            return user, "用户创建成功"

        # 捕获唯一约束异常（用户名/邮箱重复）
        except IntegrityError:
            await db.rollback()  # 异步回滚
            db_logger.warning(f"创建用户失败 - 用户名：{username}，邮箱：{email}，原因：用户名或邮箱已存在")
            return None, "用户名或邮箱已存在"

        # 捕获其他数据库异常
        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"创建用户数据库错误 - 用户名：{username}，邮箱：{email}，异常信息：{str(e)}", exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"创建用户未知异常 - 用户名：{username}，邮箱：{email}，异常信息：{str(e)}", exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_by_id(db, user_id):
        """异步根据ID查询用户"""
        db_logger.debug(f"开始异步查询用户 - 用户ID：{user_id}")
        try:
            # 异步查询推荐使用select + scalar
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                db_logger.info(f"查询用户成功 - 用户ID：{user_id}，用户名：{user.username}，邮箱：{user.email}")
            else:
                db_logger.warning(f"查询用户失败 - 用户ID：{user_id}，原因：用户不存在")

            return user

        except SQLAlchemyError as e:
            db_logger.error(f"查询用户数据库错误 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return None

        except Exception as e:
            db_logger.critical(f"查询用户未知异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return None

    @staticmethod
    async def get_user_by_username(db, username):
        """异步根据用户名查询用户"""
        db_logger.debug(f"开始异步查询用户 - 用户名：{username}")
        try:
            result = await db.execute(select(User).filter(User.username == username))
            user = result.scalar_one_or_none()

            if user:
                db_logger.info(f"查询用户成功 - 用户名：{username}，用户ID：{user.id}，邮箱：{user.email}")
            else:
                db_logger.warning(f"查询用户失败 - 用户名：{username}，原因：用户不存在")

            return user

        except SQLAlchemyError as e:
            db_logger.error(f"查询用户数据库错误 - 用户名：{username}，异常信息：{str(e)}", exc_info=True)
            return None

        except Exception as e:
            db_logger.critical(f"查询用户未知异常 - 用户名：{username}，异常信息：{str(e)}", exc_info=True)
            return None

    @staticmethod
    async def get_user_by_email(db, email):
        """异步根据邮箱查询用户"""
        db_logger.debug(f"开始异步查询用户 - 邮箱：{email}")
        try:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                db_logger.info(f"查询用户成功 - 邮箱：{email}，用户ID：{user.id}，用户名：{user.username}")
            else:
                db_logger.warning(f"查询用户失败 - 邮箱：{email}，原因：用户不存在")

            return user

        except SQLAlchemyError as e:
            db_logger.error(f"查询用户数据库错误 - 邮箱：{email}，异常信息：{str(e)}", exc_info=True)
            return None

        except Exception as e:
            db_logger.critical(f"查询用户未知异常 - 邮箱：{email}，异常信息：{str(e)}", exc_info=True)
            return None

    @staticmethod
    async def get_all_users(db, skip=0, limit=100):
        """异步查询所有用户（支持分页）"""
        db_logger.info(f"开始异步分页查询所有用户 - 跳过：{skip}，每页条数：{limit}")
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            users = result.scalars().all()
            user_count = len(users)

            db_logger.info(f"分页查询用户成功 - 共查询到 {user_count} 条用户数据，跳过：{skip}，每页条数：{limit}")
            return users

        except SQLAlchemyError as e:
            db_logger.error(f"分页查询用户数据库错误 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}", exc_info=True)
            return []

        except Exception as e:
            db_logger.critical(f"分页查询用户未知异常 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}", exc_info=True)
            return []

    @staticmethod
    async def update_user(db, user_id, **kwargs):
        """
        异步更新用户信息
        :param db: 异步数据库会话（AsyncSession）
        :param user_id: 用户ID
        :param kwargs: 要更新的字段（如 username/email/hashed_password）
        :return: (更新后的用户/None, 提示信息)
        """
        # 整理更新字段（便于日志记录）
        update_fields = [k for k, v in kwargs.items() if v]
        db_logger.info(f"开始异步更新用户 - 用户ID：{user_id}，更新字段：{','.join(update_fields)}")

        try:
            # 先查用户是否存在
            user = await db.get(User, user_id)  # 异步快捷查询（等价于按主键查询）
            if not user:
                db_logger.warning(f"更新用户失败 - 用户ID：{user_id}，原因：用户不存在")
                return None, "用户不存在"

            # 只允许更新指定字段，避免误改
            allowed_fields = ["username", "hashed_password", "email"]
            for field, value in kwargs.items():
                if field in allowed_fields and value:
                    setattr(user, field, value)
                    db_logger.debug(
                        f"用户 {user_id} 字段更新 - {field}：{value if field != 'hashed_password' else '******'}")

            await db.commit()
            await db.refresh(user)

            db_logger.info(f"更新用户成功 - 用户ID：{user_id}，更新后用户名：{user.username}，邮箱：{user.email}")
            return user, "用户信息更新成功"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(f"更新用户失败 - 用户ID：{user_id}，原因：用户名或邮箱已存在")
            return None, "用户名或邮箱已存在"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"更新用户数据库错误 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"更新用户未知异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_user(db, user_id):
        """异步删除用户"""
        db_logger.warning(f"开始异步删除用户 - 用户ID：{user_id}（物理删除）")
        try:
            user = await db.get(User, user_id)
            if not user:
                db_logger.warning(f"删除用户失败 - 用户ID：{user_id}，原因：用户不存在")
                return False, "用户不存在"

            await db.delete(user)
            await db.commit()

            db_logger.info(f"删除用户成功 - 用户ID：{user_id}，用户名：{user.username}")
            return True, "用户删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"删除用户数据库错误 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"删除用户未知异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 异步使用示例（日常开发调试/调用用）
# ------------------------------
async def test_user_crud():
    """异步测试用户CRUD操作"""
    logger.info("开始执行用户CRUD异步测试")
    # 获取异步数据库会话（需确保get_async_db是异步生成器）
    async for db in get_async_db():  # 异步生成器遍历
        try:
            # 1. 异步创建用户
            user, msg = await UserCRUD.create_user(
                db,
                username="zhangsan",
                hashed_password="hash_123456",  # 实际用加密库生成（如passlib）
                email="zhangsan@test.com"
            )
            logger.info(f"创建用户测试结果：{msg}，ID：{user.id if user else '失败'}")

            # 2. 异步查询用户
            get_user = await UserCRUD.get_user_by_id(db, user.id)
            logger.info(f"查询用户测试结果：{get_user.username} / {get_user.email}" if get_user else "查询失败")

            # 3. 异步更新用户
            update_user, msg = await UserCRUD.update_user(
                db,
                user_id=user.id,
                email="new_zhangsan@test.com"
            )
            logger.info(f"更新用户测试结果：{msg}，新邮箱：{update_user.email if update_user else '失败'}")

            # 4. 异步删除用户
            is_del, msg = await UserCRUD.delete_user(db, user.id)
            logger.info(f"删除用户测试结果：{msg}，是否成功：{is_del}")

        except Exception as e:
            logger.error(f"用户CRUD测试异常：{str(e)}", exc_info=True)
        finally:
            # 异步会话无需手动close，退出上下文会自动处理
            pass
    logger.info("用户CRUD异步测试执行完成")


# 执行异步测试（需在异步环境中运行）
if __name__ == "__main__":
    import asyncio

    # 运行异步测试函数
    asyncio.run(test_user_crud())
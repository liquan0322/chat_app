from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器

from app.db.session import get_async_db
from app.models.user import User
from app.core.logging import logger


# 用户CRUD操作类
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
        try:
            # 构建用户对象
            user = User(
                username=username,
                hashed_password=hashed_password,
                email=email
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            return user, "用户创建成功"

        # 捕获唯一约束异常
        except IntegrityError:
            await db.rollback()  # 异步回滚
            return None, "用户名或邮箱已存在"

        # 捕获其他数据库异常
        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_by_id(db, user_id):
        """异步根据ID查询用户"""
        try:
            # 异步查询推荐使用select + scalar
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            return user

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_by_username(db, username):
        """异步根据用户名查询用户"""
        try:
            result = await db.execute(select(User).filter(User.username == username))
            user = result.scalar_one_or_none()

            return user

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_by_email(db, email):
        """异步根据邮箱查询用户"""
        try:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()

            return user

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_all_users(db, skip=0, limit=100):
        """异步查询所有用户（支持分页）"""
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            users = result.scalars().all()

            return users

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def update_user(db, user_id, **kwargs):
        """
        异步更新用户信息
        :param db: 异步数据库会话（AsyncSession）
        :param user_id: 用户ID
        :param kwargs: 要更新的字段（如 username/email/hashed_password）
        :return: (更新后的用户/None, 提示信息)
        """
        # 整理更新字段
        update_fields = [k for k, v in kwargs.items() if v]

        try:
            # 先查用户是否存在
            user = await db.get(User, user_id)
            if not user:
                return None, "用户不存在"

            # 只允许更新指定字段，避免误改
            allowed_fields = ["username", "hashed_password", "email"]
            for field, value in kwargs.items():
                if field in allowed_fields and value:
                    setattr(user, field, value)

            await db.commit()
            await db.refresh(user)

            return user, "用户信息更新成功"

        except IntegrityError:
            await db.rollback()
            return None, "用户名或邮箱已存在"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_user(db, user_id):
        """异步删除用户"""
        try:
            user = await db.get(User, user_id)
            if not user:
                return False, "用户不存在"

            await db.delete(user)
            await db.commit()

            return True, "用户删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 异步使用示例
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


# 执行异步测试
if __name__ == "__main__":
    import asyncio

    # 运行异步测试函数
    asyncio.run(test_user_crud())
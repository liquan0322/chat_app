# 导入基础依赖（新增异步相关）
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器
# 导入项目已封装的异步数据库工具和AI机器人模型
from app.db.session import get_async_db  # 替换为异步数据库会话生成器
from app.models.robot import AiRobot  # 请根据实际路径调整

# ========== 核心：导入日志实例 ==========
from app.core.logging import db_logger, logger


# AI机器人CRUD操作类（全异步 + 日志集成）
class AiRobotCRUD:
    @staticmethod
    async def create_robot(db, name, role, personality=None, response_template=None):
        """
        异步创建AI机器人角色
        :param db: 异步数据库会话（AsyncSession）
        :param name: 机器人名称
        :param role: 机器人角色（客服、技术、幽默等）
        :param personality: 性格描述（可选）
        :param response_template: 回复模板（可选）
        :return: (机器人对象/None, 提示信息)
        """
        # 记录创建请求（DEBUG级别，开发环境可见）
        db_logger.debug(
            f"开始异步创建AI机器人 - 名称：{name}，角色：{role}，"
            f"性格：{personality if personality else '无'}，回复模板：{response_template[:50] + '...' if response_template and len(response_template) > 50 else response_template or '无'}"
        )
        try:
            # 构建机器人对象
            robot = AiRobot(
                name=name,
                role=role,
                personality=personality,
                response_template=response_template
            )
            db.add(robot)
            await db.commit()  # 异步提交
            await db.refresh(robot)  # 异步刷新获取自动生成字段（id/时间）

            # 记录创建成功（INFO级别，生产环境可见）
            db_logger.info(
                f"AI机器人创建成功 - 机器人ID：{robot.id}，名称：{robot.name}，角色：{robot.role}，"
                f"创建时间：{robot.created_at}"
            )
            return robot, "机器人创建成功"

        # 捕获数据库异常（如唯一约束/连接错误等）
        except IntegrityError:
            await db.rollback()  # 异步回滚
            db_logger.warning(f"创建AI机器人失败 - 名称：{name}，角色：{role}，原因：数据重复或约束异常")
            return None, "数据重复或约束异常"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(
                f"创建AI机器人数据库错误 - 名称：{name}，角色：{role}，异常信息：{str(e)}",
                exc_info=True
            )
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(
                f"创建AI机器人未知异常 - 名称：{name}，角色：{role}，异常信息：{str(e)}",
                exc_info=True
            )
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_robot_by_id(db, robot_id):
        """异步根据ID查询机器人"""
        db_logger.debug(f"开始异步查询AI机器人 - 机器人ID：{robot_id}")
        try:
            # 异步查询：select + execute + scalar_one_or_none
            result = await db.execute(select(AiRobot).filter(AiRobot.id == robot_id))
            robot = result.scalar_one_or_none()

            if robot:
                db_logger.info(
                    f"查询AI机器人成功 - 机器人ID：{robot_id}，名称：{robot.name}，角色：{robot.role}，"
                    f"性格：{robot.personality if robot.personality else '无'}"
                )
            else:
                db_logger.warning(f"查询AI机器人失败 - 机器人ID：{robot_id}，原因：机器人不存在")

            return robot

        except SQLAlchemyError as e:
            db_logger.error(
                f"查询AI机器人数据库错误 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return None

        except Exception as e:
            db_logger.critical(
                f"查询AI机器人未知异常 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return None

    @staticmethod
    async def get_robot_by_name(db, name):
        """异步根据名称查询机器人（支持精准匹配）"""
        db_logger.debug(f"开始异步查询AI机器人 - 机器人名称：{name}")
        try:
            result = await db.execute(select(AiRobot).filter(AiRobot.name == name))
            robot = result.scalar_one_or_none()

            if robot:
                db_logger.info(
                    f"查询AI机器人成功 - 名称：{name}，机器人ID：{robot.id}，角色：{robot.role}"
                )
            else:
                db_logger.warning(f"查询AI机器人失败 - 名称：{name}，原因：机器人不存在")

            return robot

        except SQLAlchemyError as e:
            db_logger.error(
                f"查询AI机器人数据库错误 - 名称：{name}，异常信息：{str(e)}",
                exc_info=True
            )
            return None

        except Exception as e:
            db_logger.critical(
                f"查询AI机器人未知异常 - 名称：{name}，异常信息：{str(e)}",
                exc_info=True
            )
            return None

    @staticmethod
    async def get_robot_by_role(db, role):
        """异步根据角色类型查询机器人（如查询所有"客服"机器人）"""
        db_logger.info(f"开始异步查询AI机器人 - 角色类型：{role}")
        try:
            result = await db.execute(select(AiRobot).filter(AiRobot.role == role))
            robots = result.scalars().all()
            robot_count = len(robots)
            robot_names = [r.name for r in robots]

            db_logger.info(
                f"按角色查询AI机器人成功 - 角色：{role}，共查询到 {robot_count} 个机器人：{','.join(robot_names)}"
            )
            return robots

        except SQLAlchemyError as e:
            db_logger.error(
                f"按角色查询AI机器人数据库错误 - 角色：{role}，异常信息：{str(e)}",
                exc_info=True
            )
            return []

        except Exception as e:
            db_logger.critical(
                f"按角色查询AI机器人未知异常 - 角色：{role}，异常信息：{str(e)}",
                exc_info=True
            )
            return []

    @staticmethod
    async def get_all_robots(db, skip=0, limit=100):
        """异步查询所有机器人（支持分页）"""
        db_logger.info(f"开始异步分页查询所有AI机器人 - 跳过：{skip}，每页条数：{limit}")
        try:
            result = await db.execute(select(AiRobot).offset(skip).limit(limit))
            robots = result.scalars().all()
            robot_count = len(robots)
            robot_ids = [str(r.id) for r in robots]

            db_logger.info(
                f"分页查询AI机器人成功 - 共查询到 {robot_count} 个机器人，跳过：{skip}，每页条数：{limit}，机器人ID：{','.join(robot_ids)}"
            )
            return robots

        except SQLAlchemyError as e:
            db_logger.error(
                f"分页查询AI机器人数据库错误 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
                exc_info=True
            )
            return []

        except Exception as e:
            db_logger.critical(
                f"分页查询AI机器人未知异常 - 跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
                exc_info=True
            )
            return []

    @staticmethod
    async def update_robot(db, robot_id, **kwargs):
        """
        异步更新机器人信息
        :param db: 异步数据库会话（AsyncSession）
        :param robot_id: 机器人ID
        :param kwargs: 要更新的字段（name/role/personality/response_template）
        :return: (更新后的机器人/None, 提示信息)
        """
        # 整理更新字段（便于日志记录）
        update_fields = [k for k, v in kwargs.items() if v is not None]
        db_logger.info(f"开始异步更新AI机器人 - 机器人ID：{robot_id}，更新字段：{','.join(update_fields)}")

        try:
            # 先查询机器人是否存在（异步快捷查询主键）
            robot = await db.get(AiRobot, robot_id)
            if not robot:
                db_logger.warning(f"更新AI机器人失败 - 机器人ID：{robot_id}，原因：机器人不存在")
                return None, "机器人不存在"

            # 仅允许更新指定字段，避免误改
            allowed_fields = ["name", "role", "personality", "response_template"]
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    old_value = getattr(robot, field)
                    setattr(robot, field, value)
                    # 回复模板过长时脱敏记录
                    log_value = value[:50] + "..." if field == "response_template" and len(str(value)) > 50 else value
                    db_logger.debug(
                        f"机器人 {robot_id} 字段更新 - {field}：{old_value if old_value else '无'} → {log_value}")

            await db.commit()
            await db.refresh(robot)

            db_logger.info(
                f"更新AI机器人成功 - 机器人ID：{robot_id}，更新后名称：{robot.name}，角色：{robot.role}"
            )
            return robot, "机器人信息更新成功"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(f"更新AI机器人失败 - 机器人ID：{robot_id}，原因：数据重复或约束异常")
            return None, "数据重复或约束异常"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(
                f"更新AI机器人数据库错误 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(
                f"更新AI机器人未知异常 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_robot(db, robot_id):
        """异步删除机器人"""
        db_logger.warning(f"开始异步删除AI机器人 - 机器人ID：{robot_id}（物理删除）")
        try:
            # 异步查询机器人是否存在
            robot = await db.get(AiRobot, robot_id)
            if not robot:
                db_logger.warning(f"删除AI机器人失败 - 机器人ID：{robot_id}，原因：机器人不存在")
                return False, "机器人不存在"

            await db.delete(robot)  # 异步删除
            await db.commit()

            db_logger.info(f"删除AI机器人成功 - 机器人ID：{robot_id}，名称：{robot.name}，角色：{robot.role}")
            return True, "机器人删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(
                f"删除AI机器人数据库错误 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(
                f"删除AI机器人未知异常 - 机器人ID：{robot_id}，异常信息：{str(e)}",
                exc_info=True
            )
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 异步使用示例（日常开发调试/调用）
# ------------------------------
async def test_ai_robot_crud():
    """异步测试AI机器人CRUD操作"""
    logger.info("开始执行AI机器人CRUD异步测试")
    # 异步获取数据库会话（异步生成器遍历）
    async for db in get_async_db():
        try:
            # 1. 异步创建机器人
            robot, msg = await AiRobotCRUD.create_robot(
                db,
                name="客服小助手",
                role="客服",
                personality="耐心、细致、专业",
                response_template="您好，请问有什么可以帮助您的？"
            )
            logger.info(f"创建机器人测试结果：{msg}，ID：{robot.id if robot else '失败'}")

            # 2. 异步根据ID查询机器人
            get_robot = await AiRobotCRUD.get_robot_by_id(db, robot.id)
            logger.info(
                f"查询机器人测试结果：{get_robot.name} / 角色：{get_robot.role}"
                if get_robot else "查询失败"
            )

            # 3. 异步根据角色查询机器人
            role_robots = await AiRobotCRUD.get_robot_by_role(db, "客服")
            logger.info(f"客服类机器人数量测试结果：{len(role_robots)}")

            # 4. 异步更新机器人（修改回复模板）
            update_robot, msg = await AiRobotCRUD.update_robot(
                db,
                robot_id=robot.id,
                response_template="您好😊，我是客服小助手，有任何问题都可以问我！"
            )
            logger.info(
                f"更新机器人测试结果：{msg}，新模板：{update_robot.response_template[:50] + '...' if update_robot else '失败'}"
            )

            # 5. 异步删除机器人
            is_del, msg = await AiRobotCRUD.delete_robot(db, robot.id)
            logger.info(f"删除机器人测试结果：{msg}，是否成功：{is_del}")

        except Exception as e:
            logger.error(f"AI机器人CRUD测试异常：{str(e)}", exc_info=True)
        finally:
            # 异步会话无需手动close，退出上下文会自动处理
            pass
    logger.info("AI机器人CRUD异步测试执行完成")


# 执行异步测试（需在异步环境中运行）
if __name__ == "__main__":
    import asyncio

    # 运行异步测试函数
    asyncio.run(test_ai_robot_crud())
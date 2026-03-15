# 导入基础依赖（新增异步相关）
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器
# 导入项目已封装的异步数据库工具和AI机器人模型
from app.db.session import get_async_db  # 替换为异步数据库会话生成器
from app.models.robot import AiRobot  # 请根据实际路径调整


# AI机器人CRUD操作类（全异步）
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
            return robot, "机器人创建成功"

        # 捕获数据库异常（如唯一约束/连接错误等）
        except IntegrityError:
            await db.rollback()  # 异步回滚
            return None, "数据重复或约束异常"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

    @staticmethod
    async def get_robot_by_id(db, robot_id):
        """异步根据ID查询机器人"""
        # 异步查询：select + execute + scalar_one_or_none
        result = await db.execute(select(AiRobot).filter(AiRobot.id == robot_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_robot_by_name(db, name):
        """异步根据名称查询机器人（支持精准匹配）"""
        result = await db.execute(select(AiRobot).filter(AiRobot.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_robot_by_role(db, role):
        """异步根据角色类型查询机器人（如查询所有"客服"机器人）"""
        result = await db.execute(select(AiRobot).filter(AiRobot.role == role))
        return result.scalars().all()

    @staticmethod
    async def get_all_robots(db, skip=0, limit=100):
        """异步查询所有机器人（支持分页）"""
        result = await db.execute(select(AiRobot).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_robot(db, robot_id, **kwargs):
        """
        异步更新机器人信息
        :param db: 异步数据库会话（AsyncSession）
        :param robot_id: 机器人ID
        :param kwargs: 要更新的字段（name/role/personality/response_template）
        :return: (更新后的机器人/None, 提示信息)
        """
        try:
            # 先查询机器人是否存在（异步快捷查询主键）
            robot = await db.get(AiRobot, robot_id)
            if not robot:
                return None, "机器人不存在"

            # 仅允许更新指定字段，避免误改
            allowed_fields = ["name", "role", "personality", "response_template"]
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(robot, field, value)

            await db.commit()
            await db.refresh(robot)
            return robot, "机器人信息更新成功"

        except IntegrityError:
            await db.rollback()
            return None, "数据重复或约束异常"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

    @staticmethod
    async def delete_robot(db, robot_id):
        """异步删除机器人"""
        try:
            # 异步查询机器人是否存在
            robot = await db.get(AiRobot, robot_id)
            if not robot:
                return False, "机器人不存在"

            await db.delete(robot)  # 异步删除
            await db.commit()
            return True, "机器人删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"


# ------------------------------
# 异步使用示例（日常开发调试/调用）
# ------------------------------
async def test_ai_robot_crud():
    """异步测试AI机器人CRUD操作"""
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
            print(f"创建机器人：{msg}，ID：{robot.id if robot else '失败'}")

            # 2. 异步根据ID查询机器人
            get_robot = await AiRobotCRUD.get_robot_by_id(db, robot.id)
            print(f"查询机器人：{get_robot.name} / 角色：{get_robot.role}")

            # 3. 异步根据角色查询机器人
            role_robots = await AiRobotCRUD.get_robot_by_role(db, "客服")
            print(f"客服类机器人数量：{len(role_robots)}")

            # 4. 异步更新机器人（修改回复模板）
            update_robot, msg = await AiRobotCRUD.update_robot(
                db,
                robot_id=robot.id,
                response_template="您好😊，我是客服小助手，有任何问题都可以问我！"
            )
            print(f"更新机器人：{msg}，新模板：{update_robot.response_template if update_robot else '失败'}")

            # 5. 异步删除机器人
            is_del, msg = await AiRobotCRUD.delete_robot(db, robot.id)
            print(f"删除机器人：{msg}，是否成功：{is_del}")

        finally:
            # 异步会话无需手动close，退出上下文会自动处理
            pass


# 执行异步测试（需在异步环境中运行）
if __name__ == "__main__":
    import asyncio
    # 运行异步测试函数
    asyncio.run(test_ai_robot_crud())
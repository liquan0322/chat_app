from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器

from app.core.logging import logger
from app.db.session import get_async_db
from app.models.group_conversation import (
    GroupConversation,
    GroupMember,
    GroupRobot,
    GroupMessage,
    GroupConversationState
)

# ------------------------------
# 群组对话 CRUD
# ------------------------------
class GroupConversationCRUD:
    @staticmethod
    async def create_group(db, creator_id, group_name):
        """
        异步创建群组对话（自动初始化状态）
        """
        try:
            # 创建群组
            group = GroupConversation(
                name=group_name,
                creator_id=creator_id
            )
            db.add(group)
            await db.commit()
            await db.refresh(group)

            # 异步调用状态初始化
            state_result, state_msg = await GroupConversationStateCRUD.init_group_state(db, group.id)

            return group, "群组创建成功（已初始化对话状态）"

        except IntegrityError:
            await db.rollback()
            return None, "外键约束异常（创建者ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_by_id(db, group_id):
        """异步根据ID查询群组（含关联状态）"""
        try:
            result = await db.execute(
                select(GroupConversation).filter(GroupConversation.id == group_id)
            )
            group = result.scalar_one_or_none()

            return group

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_created_groups(db, user_id, skip=0, limit=100):
        """异步查询用户创建的所有群组"""
        try:
            result = await db.execute(
                select(GroupConversation)
                .filter(GroupConversation.creator_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            groups = result.scalars().all()

            return groups

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def update_group_name(db, group_id, new_name):
        """异步更新群组名称"""
        try:
            # 异步主键查询
            group = await db.get(GroupConversation, group_id)
            if not group:
                return None, "群组不存在"

            group.name = new_name
            await db.commit()
            await db.refresh(group)

            return group, "群组名称更新成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_group(db, group_id):
        """异步删除群组（级联删除成员/机器人/消息/状态）"""
        try:
            group = await db.get(GroupConversation, group_id)
            if not group:
                return False, "群组不存在"

            await db.delete(group)
            await db.commit()

            return True, "群组删除成功（关联数据已级联删除）"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组成员 CRUD
# ------------------------------
class GroupMemberCRUD:
    @staticmethod
    async def add_member_to_group(db, group_id, user_id):
        """
        异步添加用户到群组（唯一约束：同一用户不能重复加入）
        """
        try:
            member = GroupMember(
                group_id=group_id,
                user_id=user_id
            )
            db.add(member)
            await db.commit()
            await db.refresh(member)

            return member, "成员添加成功"

        except IntegrityError:
            await db.rollback()
            return None, "该用户已加入此群组（不可重复添加）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_members(db, group_id):
        """异步查询群组的所有成员"""
        try:
            result = await db.execute(
                select(GroupMember).filter(GroupMember.group_id == group_id)
            )
            members = result.scalars().all()

            return members

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_groups(db, user_id):
        """异步查询用户加入的所有群组"""
        try:
            result = await db.execute(
                select(GroupMember).filter(GroupMember.user_id == user_id)
            )
            groups = result.scalars().all()

            return groups

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def remove_member_from_group(db, group_id, user_id):
        """异步将用户移出群组"""
        try:
            result = await db.execute(
                select(GroupMember)
                .filter(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == user_id
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                return False, "成员不存在于该群组"

            await db.delete(member)
            await db.commit()

            return True, "成员移出成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组机器人 CRUD
# ------------------------------
class GroupRobotCRUD:
    @staticmethod
    async def add_robot_to_group(db, group_id, robot_id):
        """
        异步添加机器人到群组（唯一约束：同一机器人不能重复加入）
        """
        try:
            group_robot = GroupRobot(
                group_id=group_id,
                robot_id=robot_id
            )
            db.add(group_robot)
            await db.commit()
            await db.refresh(group_robot)

            return group_robot, "机器人添加到群组成功"

        except IntegrityError:
            await db.rollback()
            return None, "该机器人已加入此群组（不可重复添加）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_robots(db, group_id):
        """异步查询群组的所有机器人"""
        try:
            result = await db.execute(
                select(GroupRobot).filter(GroupRobot.group_id == group_id)
            )
            robots = result.scalars().all()

            return robots

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def remove_robot_from_group(db, group_id, robot_id):
        """异步将机器人移出群组"""
        try:
            result = await db.execute(
                select(GroupRobot)
                .filter(
                    GroupRobot.group_id == group_id,
                    GroupRobot.robot_id == robot_id
                )
            )
            group_robot = result.scalar_one_or_none()
            if not group_robot:
                return False, "机器人不存在于该群组"

            await db.delete(group_robot)
            await db.commit()

            return True, "机器人移出成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组消息 CRUD
# ------------------------------
class GroupMessageCRUD:
    @staticmethod
    async def send_group_message(
            db, group_id, message, is_human,
            sender_id=None, robot_id=None, reply_to_message_id=None
    ):
        """
        异步发送群组消息（区分人类/机器人）
        """
        try:
            # 校验参数：人类/机器人ID互斥且必填
            if is_human and not sender_id:
                return None, "人类发送消息必须指定sender_id"
            if not is_human and not robot_id:
                return None, "机器人发送消息必须指定robot_id"

            msg = GroupMessage(
                group_id=group_id,
                sender_id=sender_id,
                robot_id=robot_id,
                message=message,
                is_human=is_human,
                reply_to_message_id=reply_to_message_id
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            # 异步更新群组状态
            state_result, state_msg = await GroupConversationStateCRUD.update_state_after_message(db, group_id, msg.id,
                                                                                                  is_human)

            return msg, "消息发送成功"

        except IntegrityError:
            await db.rollback()
            return None, "外键约束异常（群组/用户/机器人ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_messages(db, group_id, skip=0, limit=200):
        """异步查询群组的所有消息（按时间正序）"""
        try:
            result = await db.execute(
                select(GroupMessage)
                .filter(GroupMessage.group_id == group_id)
                .order_by(GroupMessage.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            messages = result.scalars().all()

            return messages

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def delete_group_message(db, message_id):
        """异步删除单条群组消息"""
        try:
            msg = await db.get(GroupMessage, message_id)
            if not msg:
                return False, "消息不存在"

            await db.delete(msg)
            await db.commit()

            return True, "消息删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组对话状态 CRUD
# ------------------------------
class GroupConversationStateCRUD:
    @staticmethod
    async def init_group_state(db, group_id):
        """异步初始化群组对话状态（创建群组时自动调用）"""
        try:
            state = GroupConversationState(
                group_id=group_id,
                consecutive_robot_replies=0,
                last_human_message_id=None
            )
            db.add(state)
            await db.commit()
            await db.refresh(state)

            return state, "状态初始化成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_state(db, group_id):
        """异步查询群组对话状态"""
        try:
            result = await db.execute(
                select(GroupConversationState).filter(GroupConversationState.group_id == group_id)
            )
            state = result.scalar_one_or_none()

            return state

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def update_state_after_message(db, group_id, message_id, is_human):
        """异步更新群组状态（防机器人循环）"""
        try:
            state = await db.get(GroupConversationState, group_id)
            if not state:
                return None, "群组状态不存在"

            # 人类消息：重置机器人连续回复数，记录最后人类消息ID
            if is_human:
                state.last_human_message_id = message_id
                state.consecutive_robot_replies = 0
            # 机器人消息：增加连续回复数
            else:
                state.consecutive_robot_replies += 1

            await db.commit()
            await db.refresh(state)

            return state, "状态更新成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def reset_robot_replies(db, group_id):
        """异步重置机器人连续回复数"""
        try:
            state = await db.get(GroupConversationState, group_id)
            if not state:
                return False, "群组状态不存在"

            state.consecutive_robot_replies = 0
            await db.commit()

            return True, "机器人连续回复数重置成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 关联业务示例
# ------------------------------
async def test_group_business():
    """异步测试群组完整业务流程：创建→加成员→加机器人→发消息→查状态"""
    logger.info("开始执行群组完整业务异步测试")
    # 异步获取数据库会话
    async for db in get_async_db():
        try:
            # ------------------------------
            # 1. 创建群组（自动初始化状态）
            # ------------------------------
            group, msg = await GroupConversationCRUD.create_group(
                db,
                creator_id=1,  # 假设用户ID=1已存在
                group_name="技术交流群"
            )
            logger.info(f"1. 创建群组测试结果：{msg}，群组ID：{group.id if group else '失败'}")

            # ------------------------------
            # 2. 添加成员到群组
            # ------------------------------
            member, msg = await GroupMemberCRUD.add_member_to_group(db, group.id, user_id=2)
            logger.info(f"2. 添加成员测试结果：{msg}，成员ID：{member.id if member else '失败'}")

            # ------------------------------
            # 3. 添加机器人到群组
            # ------------------------------
            group_robot, msg = await GroupRobotCRUD.add_robot_to_group(db, group.id, robot_id=1)
            logger.info(f"3. 添加机器人测试结果：{msg}，关联ID：{group_robot.id if group_robot else '失败'}")

            # ------------------------------
            # 4. 发送群组消息（人类+机器人）
            # ------------------------------
            # 人类发送消息
            human_msg, msg = await GroupMessageCRUD.send_group_message(
                db,
                group_id=group.id,
                message="大家好！",
                is_human=True,
                sender_id=1
            )
            logger.info(f"4. 发送人类消息测试结果：{msg}，消息ID：{human_msg.id if human_msg else '失败'}")

            # 机器人回复消息
            robot_msg, msg = await GroupMessageCRUD.send_group_message(
                db,
                group_id=group.id,
                message="欢迎加入技术交流群😊",
                is_human=False,
                robot_id=1,
                reply_to_message_id=human_msg.id  # 回复人类消息
            )
            logger.info(f"   发送机器人消息测试结果：{msg}，消息ID：{robot_msg.id if robot_msg else '失败'}")

            # ------------------------------
            # 5. 查询群组状态（检查机器人连续回复数）
            # ------------------------------
            state = await GroupConversationStateCRUD.get_group_state(db, group.id)
            if state:
                logger.info(
                    f"5. 群组状态测试结果：最后人类消息ID={state.last_human_message_id}，机器人连续回复数={state.consecutive_robot_replies}")
            else:
                logger.info("5. 群组状态测试结果：查询失败")

            # ------------------------------
            # 6. 查询群组所有消息
            # ------------------------------
            messages = await GroupMessageCRUD.get_group_messages(db, group.id)
            logger.info(f"6. 群组消息列表测试结果：共{len(messages)}条")

            # ------------------------------
            # 7. 清理测试数据（删除群组）
            # ------------------------------
            is_del, msg = await GroupConversationCRUD.delete_group(db, group.id)
            logger.info(f"7. 删除群组测试结果：{msg}，是否成功：{is_del}")

        except Exception as e:
            logger.error(f"群组完整业务测试异常：{str(e)}", exc_info=True)
        finally:
            # 异步会话无需手动关闭，上下文自动处理
            pass
    logger.info("群组完整业务异步测试执行完成")


# 执行异步测试（需在异步环境中运行）
if __name__ == "__main__":
    import asyncio

    # 运行异步测试函数
    asyncio.run(test_group_business())
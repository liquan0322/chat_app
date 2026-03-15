# 导入基础依赖（新增异步相关）
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器
# 导入项目已封装的异步数据库工具和模型
from app.db.session import get_async_db  # 替换为异步数据库会话生成器
from app.models.group_conversation import (  # 请根据实际路径调整
    GroupConversation,
    GroupMember,
    GroupRobot,
    GroupMessage,
    GroupConversationState
)

# ========== 核心：导入日志实例 ==========
from app.core.logging import db_logger, logger


# ------------------------------
# 群组对话 CRUD（异步版 + 日志集成）
# ------------------------------
class GroupConversationCRUD:
    @staticmethod
    async def create_group(db, creator_id, group_name):
        """
        异步创建群组对话（自动初始化状态）
        """
        db_logger.info(f"开始异步创建群组 - 创建者ID：{creator_id}，群组名称：{group_name}")
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
            db_logger.info(f"群组状态初始化结果 - 群组ID：{group.id}，状态：{state_msg}")

            db_logger.info(f"群组创建成功 - 群组ID：{group.id}，创建者ID：{creator_id}，名称：{group_name}")
            return group, "群组创建成功（已初始化对话状态）"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(
                f"创建群组失败 - 创建者ID：{creator_id}，名称：{group_name}，原因：外键约束异常（创建者ID不存在）")
            return None, "外键约束异常（创建者ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"创建群组数据库错误 - 创建者ID：{creator_id}，名称：{group_name}，异常信息：{str(e)}",
                            exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"创建群组未知异常 - 创建者ID：{creator_id}，名称：{group_name}，异常信息：{str(e)}",
                               exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_by_id(db, group_id):
        """异步根据ID查询群组（含关联状态）"""
        db_logger.debug(f"开始异步查询群组 - 群组ID：{group_id}")
        try:
            result = await db.execute(
                select(GroupConversation).filter(GroupConversation.id == group_id)
            )
            group = result.scalar_one_or_none()

            if group:
                db_logger.info(f"查询群组成功 - 群组ID：{group_id}，名称：{group.name}，创建者ID：{group.creator_id}")
            else:
                db_logger.warning(f"查询群组失败 - 群组ID：{group_id}，原因：群组不存在")

            return group

        except SQLAlchemyError as e:
            db_logger.error(f"查询群组数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None

        except Exception as e:
            db_logger.critical(f"查询群组未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None

    @staticmethod
    async def get_user_created_groups(db, user_id, skip=0, limit=100):
        """异步查询用户创建的所有群组"""
        db_logger.info(f"开始异步分页查询用户创建的群组 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}")
        try:
            result = await db.execute(
                select(GroupConversation)
                .filter(GroupConversation.creator_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            groups = result.scalars().all()
            group_count = len(groups)
            group_ids = [str(g.id) for g in groups]

            db_logger.info(
                f"分页查询用户创建群组成功 - 用户ID：{user_id}，共查询到 {group_count} 个群组：{','.join(group_ids)}，跳过：{skip}，每页条数：{limit}")
            return groups

        except SQLAlchemyError as e:
            db_logger.error(
                f"分页查询用户创建群组数据库错误 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
                exc_info=True)
            return []

        except Exception as e:
            db_logger.critical(
                f"分页查询用户创建群组未知异常 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
                exc_info=True)
            return []

    @staticmethod
    async def update_group_name(db, group_id, new_name):
        """异步更新群组名称"""
        db_logger.info(f"开始异步更新群组名称 - 群组ID：{group_id}，新名称：{new_name}")
        try:
            # 异步主键查询
            group = await db.get(GroupConversation, group_id)
            if not group:
                db_logger.warning(f"更新群组名称失败 - 群组ID：{group_id}，原因：群组不存在")
                return None, "群组不存在"

            old_name = group.name
            group.name = new_name
            await db.commit()
            await db.refresh(group)

            db_logger.info(f"更新群组名称成功 - 群组ID：{group_id}，旧名称：{old_name} → 新名称：{new_name}")
            return group, "群组名称更新成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"更新群组名称数据库错误 - 群组ID：{group_id}，新名称：{new_name}，异常信息：{str(e)}",
                            exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"更新群组名称未知异常 - 群组ID：{group_id}，新名称：{new_name}，异常信息：{str(e)}",
                               exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_group(db, group_id):
        """异步删除群组（级联删除成员/机器人/消息/状态）"""
        db_logger.warning(f"开始异步删除群组 - 群组ID：{group_id}（级联删除成员/机器人/消息/状态）")
        try:
            group = await db.get(GroupConversation, group_id)
            if not group:
                db_logger.warning(f"删除群组失败 - 群组ID：{group_id}，原因：群组不存在")
                return False, "群组不存在"

            await db.delete(group)
            await db.commit()

            db_logger.info(f"删除群组成功 - 群组ID：{group_id}，名称：{group.name}，已级联删除所有关联数据")
            return True, "群组删除成功（关联数据已级联删除）"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"删除群组数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"删除群组未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组成员 CRUD（异步版 + 日志集成）
# ------------------------------
class GroupMemberCRUD:
    @staticmethod
    async def add_member_to_group(db, group_id, user_id):
        """
        异步添加用户到群组（唯一约束：同一用户不能重复加入）
        """
        db_logger.info(f"开始异步添加群组成员 - 群组ID：{group_id}，用户ID：{user_id}")
        try:
            member = GroupMember(
                group_id=group_id,
                user_id=user_id
            )
            db.add(member)
            await db.commit()
            await db.refresh(member)

            db_logger.info(f"添加群组成员成功 - 成员ID：{member.id}，群组ID：{group_id}，用户ID：{user_id}")
            return member, "成员添加成功"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(
                f"添加群组成员失败 - 群组ID：{group_id}，用户ID：{user_id}，原因：该用户已加入此群组（不可重复添加）")
            return None, "该用户已加入此群组（不可重复添加）"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"添加群组成员数据库错误 - 群组ID：{group_id}，用户ID：{user_id}，异常信息：{str(e)}",
                            exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"添加群组成员未知异常 - 群组ID：{group_id}，用户ID：{user_id}，异常信息：{str(e)}",
                               exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_members(db, group_id):
        """异步查询群组的所有成员"""
        db_logger.debug(f"开始异步查询群组成员 - 群组ID：{group_id}")
        try:
            result = await db.execute(
                select(GroupMember).filter(GroupMember.group_id == group_id)
            )
            members = result.scalars().all()
            member_count = len(members)
            member_ids = [str(m.user_id) for m in members]

            db_logger.info(
                f"查询群组成员成功 - 群组ID：{group_id}，共查询到 {member_count} 个成员：{','.join(member_ids)}")
            return members

        except SQLAlchemyError as e:
            db_logger.error(f"查询群组成员数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return []

        except Exception as e:
            db_logger.critical(f"查询群组成员未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_user_groups(db, user_id):
        """异步查询用户加入的所有群组"""
        db_logger.info(f"开始异步查询用户加入的群组 - 用户ID：{user_id}")
        try:
            result = await db.execute(
                select(GroupMember).filter(GroupMember.user_id == user_id)
            )
            groups = result.scalars().all()
            group_count = len(groups)
            group_ids = [str(g.group_id) for g in groups]

            db_logger.info(f"查询用户加入群组成功 - 用户ID：{user_id}，共加入 {group_count} 个群组：{','.join(group_ids)}")
            return groups

        except SQLAlchemyError as e:
            db_logger.error(f"查询用户加入群组数据库错误 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return []

        except Exception as e:
            db_logger.critical(f"查询用户加入群组未知异常 - 用户ID：{user_id}，异常信息：{str(e)}", exc_info=True)
            return []

    @staticmethod
    async def remove_member_from_group(db, group_id, user_id):
        """异步将用户移出群组"""
        db_logger.warning(f"开始异步移出群组成员 - 群组ID：{group_id}，用户ID：{user_id}")
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
                db_logger.warning(f"移出群组成员失败 - 群组ID：{group_id}，用户ID：{user_id}，原因：成员不存在于该群组")
                return False, "成员不存在于该群组"

            await db.delete(member)
            await db.commit()

            db_logger.info(f"移出群组成员成功 - 群组ID：{group_id}，用户ID：{user_id}")
            return True, "成员移出成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"移出群组成员数据库错误 - 群组ID：{group_id}，用户ID：{user_id}，异常信息：{str(e)}",
                            exc_info=True)
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"移出群组成员未知异常 - 群组ID：{group_id}，用户ID：{user_id}，异常信息：{str(e)}",
                               exc_info=True)
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组机器人 CRUD（异步版 + 日志集成）
# ------------------------------
class GroupRobotCRUD:
    @staticmethod
    async def add_robot_to_group(db, group_id, robot_id):
        """
        异步添加机器人到群组（唯一约束：同一机器人不能重复加入）
        """
        db_logger.info(f"开始异步添加群组机器人 - 群组ID：{group_id}，机器人ID：{robot_id}")
        try:
            group_robot = GroupRobot(
                group_id=group_id,
                robot_id=robot_id
            )
            db.add(group_robot)
            await db.commit()
            await db.refresh(group_robot)

            db_logger.info(f"添加群组机器人成功 - 关联ID：{group_robot.id}，群组ID：{group_id}，机器人ID：{robot_id}")
            return group_robot, "机器人添加到群组成功"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(
                f"添加群组机器人失败 - 群组ID：{group_id}，机器人ID：{robot_id}，原因：该机器人已加入此群组（不可重复添加）")
            return None, "该机器人已加入此群组（不可重复添加）"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"添加群组机器人数据库错误 - 群组ID：{group_id}，机器人ID：{robot_id}，异常信息：{str(e)}",
                            exc_info=True)
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"添加群组机器人未知异常 - 群组ID：{group_id}，机器人ID：{robot_id}，异常信息：{str(e)}",
                               exc_info=True)
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_robots(db, group_id):
        """异步查询群组的所有机器人"""
        db_logger.debug(f"开始异步查询群组机器人 - 群组ID：{group_id}")
        try:
            result = await db.execute(
                select(GroupRobot).filter(GroupRobot.group_id == group_id)
            )
            robots = result.scalars().all()
            robot_count = len(robots)
            robot_ids = [str(r.robot_id) for r in robots]

            db_logger.info(
                f"查询群组机器人成功 - 群组ID：{group_id}，共查询到 {robot_count} 个机器人：{','.join(robot_ids)}")
            return robots

        except SQLAlchemyError as e:
            db_logger.error(f"查询群组机器人数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return []

        except Exception as e:
            db_logger.critical(f"查询群组机器人未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return []

    @staticmethod
    async def remove_robot_from_group(db, group_id, robot_id):
        """异步将机器人移出群组"""
        db_logger.warning(f"开始异步移出群组机器人 - 群组ID：{group_id}，机器人ID：{robot_id}")
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
                db_logger.warning(
                    f"移出群组机器人失败 - 群组ID：{group_id}，机器人ID：{robot_id}，原因：机器人不存在于该群组")
                return False, "机器人不存在于该群组"

            await db.delete(group_robot)
            await db.commit()

            db_logger.info(f"移出群组机器人成功 - 群组ID：{group_id}，机器人ID：{robot_id}")
            return True, "机器人移出成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"移出群组机器人数据库错误 - 群组ID：{group_id}，机器人ID：{robot_id}，异常信息：{str(e)}",
                            exc_info=True)
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"移出群组机器人未知异常 - 群组ID：{group_id}，机器人ID：{robot_id}，异常信息：{str(e)}",
                               exc_info=True)
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组消息 CRUD（异步版 + 日志集成）
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
        # 消息内容脱敏
        msg_content = message[:50] + "..." if len(message) > 50 else message
        sender_type = "人类" if is_human else "机器人"
        sender_id_log = sender_id if is_human else robot_id
        reply_log = reply_to_message_id if reply_to_message_id else "无"

        db_logger.info(
            f"开始异步发送群组消息 - 群组ID：{group_id}，发送方：{sender_type}({sender_id_log})，"
            f"回复消息ID：{reply_log}，消息内容：{msg_content}"
        )

        try:
            # 校验参数：人类/机器人ID互斥且必填
            if is_human and not sender_id:
                db_logger.warning(f"发送群组消息参数错误 - 群组ID：{group_id}，人类消息未指定sender_id")
                return None, "人类发送消息必须指定sender_id"
            if not is_human and not robot_id:
                db_logger.warning(f"发送群组消息参数错误 - 群组ID：{group_id}，机器人消息未指定robot_id")
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
            db_logger.info(f"群组状态更新结果 - 群组ID：{group_id}，消息ID：{msg.id}，状态：{state_msg}")

            db_logger.info(
                f"发送群组消息成功 - 消息ID：{msg.id}，群组ID：{group_id}，发送方：{sender_type}({sender_id_log})")
            return msg, "消息发送成功"

        except IntegrityError:
            await db.rollback()
            db_logger.warning(
                f"发送群组消息失败 - 群组ID：{group_id}，发送方：{sender_type}({sender_id_log})，"
                f"原因：外键约束异常（群组/用户/机器人ID不存在）"
            )
            return None, "外键约束异常（群组/用户/机器人ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(
                f"发送群组消息数据库错误 - 群组ID：{group_id}，发送方：{sender_type}({sender_id_log})，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(
                f"发送群组消息未知异常 - 群组ID：{group_id}，发送方：{sender_type}({sender_id_log})，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_group_messages(db, group_id, skip=0, limit=200):
        """异步查询群组的所有消息（按时间正序）"""
        db_logger.info(f"开始异步查询群组消息 - 群组ID：{group_id}，跳过：{skip}，每页条数：{limit}")
        try:
            result = await db.execute(
                select(GroupMessage)
                .filter(GroupMessage.group_id == group_id)
                .order_by(GroupMessage.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            messages = result.scalars().all()
            msg_count = len(messages)

            db_logger.info(
                f"查询群组消息成功 - 群组ID：{group_id}，共查询到 {msg_count} 条消息，跳过：{skip}，每页条数：{limit}")
            return messages

        except SQLAlchemyError as e:
            db_logger.error(
                f"查询群组消息数据库错误 - 群组ID：{group_id}，跳过：{skip}，每页条数：{limit}，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return []

        except Exception as e:
            db_logger.critical(
                f"查询群组消息未知异常 - 群组ID：{group_id}，跳过：{skip}，每页条数：{limit}，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return []

    @staticmethod
    async def delete_group_message(db, message_id):
        """异步删除单条群组消息"""
        db_logger.warning(f"开始异步删除群组消息 - 消息ID：{message_id}")
        try:
            msg = await db.get(GroupMessage, message_id)
            if not msg:
                db_logger.warning(f"删除群组消息失败 - 消息ID：{message_id}，原因：消息不存在")
                return False, "消息不存在"

            await db.delete(msg)
            await db.commit()

            db_logger.info(f"删除群组消息成功 - 消息ID：{message_id}，群组ID：{msg.group_id}")
            return True, "消息删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"删除群组消息数据库错误 - 消息ID：{message_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"删除群组消息未知异常 - 消息ID：{message_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 群组对话状态 CRUD（异步版 + 日志集成）
# ------------------------------
class GroupConversationStateCRUD:
    @staticmethod
    async def init_group_state(db, group_id):
        """异步初始化群组对话状态（创建群组时自动调用）"""
        db_logger.debug(f"开始异步初始化群组状态 - 群组ID：{group_id}")
        try:
            state = GroupConversationState(
                group_id=group_id,
                consecutive_robot_replies=0,
                last_human_message_id=None
            )
            db.add(state)
            await db.commit()
            await db.refresh(state)

            db_logger.info(f"初始化群组状态成功 - 群组ID：{group_id}，状态ID：{state.id}，初始机器人连续回复数：0")
            return state, "状态初始化成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"初始化群组状态数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None, f"状态初始化失败：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"初始化群组状态未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None, f"状态初始化失败：{str(e)}"

    @staticmethod
    async def get_group_state(db, group_id):
        """异步查询群组对话状态"""
        db_logger.debug(f"开始异步查询群组状态 - 群组ID：{group_id}")
        try:
            result = await db.execute(
                select(GroupConversationState).filter(GroupConversationState.group_id == group_id)
            )
            state = result.scalar_one_or_none()

            if state:
                db_logger.info(
                    f"查询群组状态成功 - 群组ID：{group_id}，机器人连续回复数：{state.consecutive_robot_replies}，"
                    f"最后人类消息ID：{state.last_human_message_id if state.last_human_message_id else '无'}"
                )
            else:
                db_logger.warning(f"查询群组状态失败 - 群组ID：{group_id}，原因：群组状态不存在")

            return state

        except SQLAlchemyError as e:
            db_logger.error(f"查询群组状态数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None

        except Exception as e:
            db_logger.critical(f"查询群组状态未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return None

    @staticmethod
    async def update_state_after_message(db, group_id, message_id, is_human):
        """异步更新群组状态（防机器人循环）"""
        db_logger.debug(
            f"开始异步更新群组状态 - 群组ID：{group_id}，消息ID：{message_id}，发送方：{'人类' if is_human else '机器人'}"
        )
        try:
            state = await db.get(GroupConversationState, group_id)
            if not state:
                db_logger.warning(f"更新群组状态失败 - 群组ID：{group_id}，原因：群组状态不存在")
                return None, "群组状态不存在"

            # 记录更新前状态
            old_replies = state.consecutive_robot_replies
            old_last_human = state.last_human_message_id

            # 人类消息：重置机器人连续回复数，记录最后人类消息ID
            if is_human:
                state.last_human_message_id = message_id
                state.consecutive_robot_replies = 0
                log_msg = f"人类消息触发状态更新 - 重置机器人连续回复数：{old_replies} → 0，记录最后人类消息ID：{message_id}"
            # 机器人消息：增加连续回复数
            else:
                state.consecutive_robot_replies += 1
                log_msg = f"机器人消息触发状态更新 - 机器人连续回复数：{old_replies} → {state.consecutive_robot_replies}"

            await db.commit()
            await db.refresh(state)

            db_logger.info(f"更新群组状态成功 - 群组ID：{group_id}，{log_msg}")
            return state, "状态更新成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(
                f"更新群组状态数据库错误 - 群组ID：{group_id}，消息ID：{message_id}，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return None, f"状态更新失败：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(
                f"更新群组状态未知异常 - 群组ID：{group_id}，消息ID：{message_id}，"
                f"异常信息：{str(e)}", exc_info=True
            )
            return None, f"状态更新失败：{str(e)}"

    @staticmethod
    async def reset_robot_replies(db, group_id):
        """异步重置机器人连续回复数"""
        db_logger.info(f"开始异步重置机器人连续回复数 - 群组ID：{group_id}")
        try:
            state = await db.get(GroupConversationState, group_id)
            if not state:
                db_logger.warning(f"重置机器人回复数失败 - 群组ID：{group_id}，原因：群组状态不存在")
                return False, "群组状态不存在"

            old_count = state.consecutive_robot_replies
            state.consecutive_robot_replies = 0
            await db.commit()

            db_logger.info(f"重置机器人连续回复数成功 - 群组ID：{group_id}，回复数：{old_count} → 0")
            return True, "机器人连续回复数重置成功"

        except SQLAlchemyError as e:
            await db.rollback()
            db_logger.error(f"重置机器人回复数数据库错误 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"重置失败：{str(e)}"

        except Exception as e:
            await db.rollback()
            db_logger.critical(f"重置机器人回复数未知异常 - 群组ID：{group_id}，异常信息：{str(e)}", exc_info=True)
            return False, f"重置失败：{str(e)}"


# ------------------------------
# 关联业务示例（异步版 + 日志集成）
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
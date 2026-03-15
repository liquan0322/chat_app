from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select  # 异步查询推荐使用select构造器

from app.core.logging import logger
from app.db.session import get_async_db
from app.models.individual_conversation import (
    IndividualConversation,
    ConversationTag,
    IndividualMessage
)


# ------------------------------
# 个人对话 CRUD
# ------------------------------
class IndividualConversationCRUD:
    @staticmethod
    async def create_conversation(db, user_id, title):
        """
        异步创建个人对话
        :param db: 异步数据库会话（AsyncSession）
        :param user_id: 所属用户ID
        :param title: 对话标题
        :return: (对话对象/None, 提示信息)
        """
        try:
            conversation = IndividualConversation(
                user_id=user_id,
                title=title
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            return conversation, "对话创建成功"

        except IntegrityError:
            await db.rollback()  # 异步回滚
            return None, "外键约束异常（用户ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_conversation_by_id(db, conversation_id):
        """异步根据ID查询对话"""
        try:
            result = await db.execute(
                select(IndividualConversation).filter(IndividualConversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            return conversation

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_conversations(db, user_id, skip=0, limit=100):
        """异步查询指定用户的所有对话（分页）"""
        try:
            result = await db.execute(
                select(IndividualConversation)
                .filter(IndividualConversation.user_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            conversations = result.scalars().all()

            return conversations

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def update_conversation_title(db, conversation_id, new_title):
        """异步更新对话标题"""
        try:
            # 异步主键查询
            conversation = await db.get(IndividualConversation, conversation_id)
            if not conversation:
                return None, "对话不存在"

            conversation.title = new_title
            await db.commit()
            await db.refresh(conversation)

            return conversation, "对话标题更新成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def delete_conversation(db, conversation_id):
        """异步删除对话（会级联删除关联的标签和消息）"""
        try:
            conversation = await db.get(IndividualConversation, conversation_id)
            if not conversation:
                return False, "对话不存在"

            await db.delete(conversation)  # 异步删除
            await db.commit()

            return True, "对话删除成功（关联标签/消息已级联删除）"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 对话标签 CRUD
# ------------------------------
class ConversationTagCRUD:
    @staticmethod
    async def add_tag_to_conversation(db, conversation_id, tag, user_id):
        """
        异步给对话添加标签（唯一约束：同一对话不能重复标签）
        """
        try:
            conversation_tag = ConversationTag(
                conversation_id=conversation_id,
                tag=tag,
                user_id=user_id
            )
            db.add(conversation_tag)
            await db.commit()
            await db.refresh(conversation_tag)

            return conversation_tag, "标签添加成功"

        except IntegrityError:
            await db.rollback()
            return None, "该对话已添加此标签（标签不可重复）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_conversation_tags(db, conversation_id):
        """异步查询指定对话的所有标签"""
        try:
            result = await db.execute(
                select(ConversationTag).filter(ConversationTag.conversation_id == conversation_id)
            )
            tags = result.scalars().all()

            return tags

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def get_user_tags(db, user_id):
        """异步查询指定用户的所有标签（去重）"""
        try:
            result = await db.execute(
                select(ConversationTag.tag)
                .filter(ConversationTag.user_id == user_id)
                .distinct()
            )
            # 提取标签值（原同步返回的是元组列表，保持格式一致）
            tag_list = [(tag,) for tag in result.scalars().all()]

            return tag_list

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def get_conversations_by_tag(db, user_id, tag):
        """异步根据标签查询用户的对应对话（关联查询）"""
        try:
            result = await db.execute(
                select(IndividualConversation)
                .join(ConversationTag, IndividualConversation.id == ConversationTag.conversation_id)
                .filter(
                    ConversationTag.user_id == user_id,
                    ConversationTag.tag == tag
                )
            )
            conversations = result.scalars().all()

            return conversations

        except SQLAlchemyError as e:
            await db.rollback()
            return [], f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return [], f"系统错误：{str(e)}"

    @staticmethod
    async def delete_conversation_tag(db, conversation_id, tag):
        """异步删除对话的指定标签"""
        try:
            result = await db.execute(
                select(ConversationTag)
                .filter(
                    ConversationTag.conversation_id == conversation_id,
                    ConversationTag.tag == tag
                )
            )
            tag_obj = result.scalar_one_or_none()
            if not tag_obj:
                return False, "标签不存在"

            await db.delete(tag_obj)
            await db.commit()

            return True, "标签删除成功"

        except SQLAlchemyError as e:
            await db.rollback()
            return False, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return False, f"系统错误：{str(e)}"


# ------------------------------
# 个人消息 CRUD
# ------------------------------
class IndividualMessageCRUD:
    @staticmethod
    async def send_message(db, conversation_id, user_id, message, is_user_message, ai_error=None):
        """异步发送个人消息（用户/AI消息）"""
        try:
            msg = IndividualMessage(
                conversation_id=conversation_id,
                user_id=user_id,
                message=message,
                is_user_message=is_user_message,
                ai_error=ai_error
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            return msg, "消息发送成功"

        except IntegrityError:
            await db.rollback()
            return None, "外键约束异常（对话/用户ID不存在）"

        except SQLAlchemyError as e:
            await db.rollback()
            return None, f"数据库错误：{str(e)}"

        except Exception as e:
            await db.rollback()
            return None, f"系统错误：{str(e)}"

    @staticmethod
    async def get_conversation_messages(db, conversation_id, skip=0, limit=200):
        """异步查询指定对话的所有消息（按时间正序）"""
        try:
            result = await db.execute(
                select(IndividualMessage)
                .filter(IndividualMessage.conversation_id == conversation_id)
                .order_by(IndividualMessage.created_at.asc())
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
    async def delete_message(db, message_id):
        """异步删除单条消息"""
        try:
            msg = await db.get(IndividualMessage, message_id)
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
# 关联业务示例
# ------------------------------
async def test_conversation_business():
    """异步测试对话+标签+消息的关联业务流程"""
    logger.info("开始执行个人对话关联业务异步测试")
    # 异步获取数据库会话
    async for db in get_async_db():
        try:
            # ------------------------------
            # 1. 创建对话
            # ------------------------------
            conversation, msg = await IndividualConversationCRUD.create_conversation(
                db,
                user_id=1,  # 假设用户ID=1已存在
                title="技术问题咨询"
            )
            logger.info(f"1. 创建对话测试结果：{msg}，对话ID：{conversation.id if conversation else '失败'}")

            # ------------------------------
            # 2. 给对话添加标签
            # ------------------------------
            tag, msg = await ConversationTagCRUD.add_tag_to_conversation(
                db,
                conversation_id=conversation.id,
                tag="技术",
                user_id=1
            )
            logger.info(f"2. 添加标签测试结果：{msg}")

            # ------------------------------
            # 3. 发送消息（用户消息+AI消息）
            # ------------------------------
            # 用户发送消息
            user_msg, msg = await IndividualMessageCRUD.send_message(
                db,
                conversation_id=conversation.id,
                user_id=1,
                message="Python怎么连接MySQL？",
                is_user_message=True
            )
            logger.info(f"3. 发送用户消息测试结果：{msg}，消息ID：{user_msg.id if user_msg else '失败'}")

            # AI回复消息
            ai_msg, msg = await IndividualMessageCRUD.send_message(
                db,
                conversation_id=conversation.id,
                user_id=1,  # AI消息也关联到用户ID
                message="可以使用pymysql库，示例：import pymysql; conn = pymysql.connect(...)",
                is_user_message=False
            )
            logger.info(f"   发送AI消息测试结果：{msg}，消息ID：{ai_msg.id if ai_msg else '失败'}")

            # ------------------------------
            # 4. 查询对话的所有消息
            # ------------------------------
            messages = await IndividualMessageCRUD.get_conversation_messages(db, conversation.id)
            logger.info(f"4. 对话消息列表测试结果：共{len(messages)}条")

            # ------------------------------
            # 5. 根据标签查询对话
            # ------------------------------
            tag_conversations = await ConversationTagCRUD.get_conversations_by_tag(db, 1, "技术")
            logger.info(f"5. 标签'技术'下的对话数量测试结果：{len(tag_conversations)}")

            # ------------------------------
            # 6. 清理测试数据（删除对话，级联删除标签/消息）
            # ------------------------------
            is_del, msg = await IndividualConversationCRUD.delete_conversation(db, conversation.id)
            logger.info(f"6. 删除对话测试结果：{msg}，是否成功：{is_del}")

        except Exception as e:
            logger.error(f"个人对话关联业务测试异常：{str(e)}", exc_info=True)
        finally:
            # 异步会话无需手动关闭，上下文自动处理
            pass
    logger.info("个人对话关联业务异步测试执行完成")


# 执行异步测试（需在异步环境中运行）
if __name__ == "__main__":
    import asyncio

    # 运行异步测试函数
    asyncio.run(test_conversation_business())
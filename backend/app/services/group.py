import asyncio
import logging
import random
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app import crud, models, schemas
from app.services.ai_client import AIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class GroupMessageService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClient()
        # 防循环配置
        self.max_robot_consecutive_replies = settings.MAX_ROBOT_CONSECUTIVE_REPLIES
        self.robot_response_strategy = settings.ROBOT_RESPONSE_STRATEGY  # all/random/single

    async def process_group_message(
            self,
            group_id: UUID,
            sender_id: UUID,
            message_content: str
    ) -> List[schemas.Message]:
        """
        处理群组消息，触发机器人回复
        """
        # 1. 保存用户消息
        user_message = await self._save_user_message(group_id, sender_id, message_content)

        # 2. 获取群组中的机器人列表
        group_robots = await self._get_group_robots(group_id)
        if not group_robots:
            raise ValueError("Group has no robots assigned")

        # 3. 检查机器人回复限制（防循环）
        if not await self._can_robots_reply(group_id):
            # 即使不能回复，也要确保至少有一个简单回复
            return [user_message] + await self._get_fallback_robot_reply(group_id, group_robots[0])

        # 4. 根据策略选择回复的机器人
        selected_robots = await self._select_robots_for_response(group_robots)

        # 5. 触发机器人回复
        robot_messages = []
        for robot in selected_robots:
            robot_message = await self._get_robot_reply(
                group_id=group_id,
                robot=robot,
                user_message=message_content
            )
            robot_messages.append(robot_message)

        # 6. 如果没有机器人回复成功，添加备用回复
        if not any(not msg.is_error for msg in robot_messages):
            robot_messages = await self._get_fallback_robot_reply(group_id, group_robots[0])

        return [user_message] + robot_messages

    async def _save_user_message(
            self,
            group_id: UUID,
            sender_id: UUID,
            message_content: str
    ) -> schemas.Message:
        """保存用户消息到数据库"""
        # 获取群组对应的conversation_id
        group = crud.group.get(self.db, id=group_id)
        conversation_id = group.conversation_id

        message_in = schemas.MessageCreate(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type="user",
            content=message_content,
            is_error=False
        )
        return crud.message.create(self.db, obj_in=message_in)

    async def _get_group_robots(self, group_id: UUID) -> List[models.Robot]:
        """获取群组中的所有机器人"""
        group_members = crud.group_member.get_multi_by_group(
            self.db,
            group_id=group_id,
            member_type="robot"
        )
        return [member.robot for member in group_members]

    async def _can_robots_reply(self, group_id: UUID) -> bool:
        """检查机器人是否可以回复（防循环）"""
        # 获取群组对应的conversation_id
        group = crud.group.get(self.db, id=group_id)
        conversation_id = group.conversation_id

        # 获取最新的N条消息
        latest_messages = crud.message.get_multi_by_conversation(
            self.db,
            conversation_id=conversation_id,
            skip=0,
            limit=self.max_robot_consecutive_replies + 1
        )

        # 统计连续的机器人回复数量
        consecutive_robot_replies = 0
        for msg in latest_messages:
            if msg.sender_type == "robot":
                consecutive_robot_replies += 1
            else:
                break

        return consecutive_robot_replies < self.max_robot_consecutive_replies

    async def _select_robots_for_response(
            self,
            robots: List[models.Robot]
    ) -> List[models.Robot]:
        """根据策略选择要回复的机器人"""
        if self.robot_response_strategy == "all":
            return robots
        elif self.robot_response_strategy == "random":
            # 随机选择1-N个机器人
            num_robots = random.randint(1, min(3, len(robots)))
            return random.sample(robots, num_robots)
        elif self.robot_response_strategy == "single":
            # 随机选择一个机器人
            return [random.choice(robots)]
        else:
            # 默认返回第一个机器人
            return [robots[0]]

    async def _get_robot_reply(
            self,
            group_id: UUID,
            robot: models.Robot,
            user_message: str
    ) -> schemas.Message:
        """获取单个机器人的回复"""
        # 获取群组对应的conversation_id
        group = crud.group.get(self.db, id=group_id)
        conversation_id = group.conversation_id

        try:
            # 调用AI API获取回复
            ai_response = await self.ai_client.get_ai_response(
                message=user_message,
                robot_personality=robot.personality,
                conversation_id=str(conversation_id)
            )

            if ai_response["success"]:
                content = ai_response["content"]
                is_error = False
                error_message = None
            else:
                content = ai_response["content"] or "抱歉，我无法回复你的消息。"
                is_error = True
                error_message = ai_response["error"]

        except Exception as e:
            # 所有重试都失败后的处理
            fallback_response = await self.ai_client.get_fallback_response(str(e))
            content = fallback_response["content"]
            is_error = True
            error_message = fallback_response["error"]
            logger.error(f"Robot {robot.name} failed to respond: {str(e)}")

        # 保存机器人回复
        message_in = schemas.MessageCreate(
            conversation_id=conversation_id,
            sender_id=robot.id,
            sender_type="robot",
            content=content,
            is_error=is_error,
            error_message=error_message
        )
        return crud.message.create(self.db, obj_in=message_in)

    async def _get_fallback_robot_reply(
            self,
            group_id: UUID,
            robot: models.Robot
    ) -> List[schemas.Message]:
        """获取备用的机器人回复（确保至少有一个回复）"""
        group = crud.group.get(self.db, id=group_id)
        conversation_id = group.conversation_id

        message_in = schemas.MessageCreate(
            conversation_id=conversation_id,
            sender_id=robot.id,
            sender_type="robot",
            content="当前无法处理你的请求，请等待人类用户再次发言后重试。",
            is_error=True,
            error_message="Robot reply limit exceeded (anti-loop protection)"
        )
        return [crud.message.create(self.db, obj_in=message_in)]
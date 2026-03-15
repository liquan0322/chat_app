import asyncio
import logging
from typing import Optional, Dict, Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        self.base_url = settings.AI_API_BASE_URL
        self.api_key = settings.AI_API_KEY
        self.timeout = settings.AI_API_TIMEOUT
        self.max_retries = settings.AI_API_MAX_RETRIES

    @retry(
        stop=stop_after_attempt(settings.AI_API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def get_ai_response(
            self,
            message: str,
            robot_personality: Optional[str] = None,
            conversation_id: Optional[str] = None
    ):
        """
        调用AI API获取回复，包含重试机制
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体，加入机器人性格参数
        payload = {
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        # 如果指定了机器人性格，添加到提示词中
        if robot_personality:
            payload["messages"].insert(
                0,
                {"role": "system", "content": f"You are a {robot_personality}. Respond in this style."}
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "error": None
                }

        except httpx.TimeoutException as e:
            logger.error(f"AI API timeout for conversation {conversation_id}: {str(e)}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"AI API returned error status {e.response.status_code} for conversation {conversation_id}: {e.response.text}")
            return {
                "success": False,
                "content": None,
                "error": f"AI API error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Unexpected error calling AI API for conversation {conversation_id}: {str(e)}")
            raise

    async def get_fallback_response(self, error):
        """
        AI API调用失败时的备用回复
        """
        return {
            "success": False,
            "content": "抱歉，我现在暂时无法回复你的消息，请稍后再试。",
            "error": error
        }
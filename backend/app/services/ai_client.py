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

# 导入自定义日志模块（核心修复：补充logger导入）
from app.core.logging import logger
from app.core.config import settings


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
        before_sleep=before_sleep_log(logger, logging.WARNING),  # 使用导入的logger
        reraise=True,
    )
    async def get_ai_response(
            self,
            message: str,
            robot_personality: Optional[str] = None,
            conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:  # 补充返回值类型注解
        """
        调用AI API获取回复，包含重试机制
        :param message: 用户输入消息
        :param robot_personality: 机器人性格描述
        :param conversation_id: 会话ID（用于日志追踪）
        :return: 包含success/content/error的响应字典
        """
        # 记录请求开始（DEBUG级别，开发环境可见）
        logger.debug(
            "开始调用AI API",
            extra={
                "conversation_id": conversation_id,
                "message_length": len(message),
                "robot_personality": robot_personality
            }
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体
        payload = {
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 1000
        }

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

                # 记录请求成功（INFO级别）
                logger.info(
                    "AI API调用成功",
                    extra={
                        "conversation_id": conversation_id,
                        "response_tokens": len(data["choices"][0]["message"]["content"])
                    }
                )

                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "error": None
                }

        except httpx.TimeoutException as e:
            logger.error(
                f"AI API请求超时",
                extra={
                    "conversation_id": conversation_id,
                    "timeout": self.timeout,
                    "error": str(e)
                }
            )
            raise  # 重新抛出，触发重试
        except httpx.HTTPStatusError as e:
            logger.error(
                f"AI API返回非2xx状态码",
                extra={
                    "conversation_id": conversation_id,
                    "status_code": e.response.status_code,
                    "response_text": e.response.text[:200],  # 截断过长的错误信息
                    "error": str(e)
                }
            )
            return await self.get_fallback_response(f"API错误：{e.response.status_code}")
        except Exception as e:
            logger.error(
                f"AI API调用出现未知异常",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e),
                    "exception_type": type(e).__name__
                },
                exc_info=True  # 记录完整异常栈（便于调试）
            )
            return await self.get_fallback_response(f"系统异常：{str(e)}")

    async def get_fallback_response(self, error: str) -> Dict[str, Any]:
        """
        AI API调用失败时的备用回复
        :param error: 错误信息
        :return: 友好的失败响应
        """
        logger.warning(
            "使用备用回复",
            extra={"error": error}
        )
        return {
            "success": False,
            "content": "抱歉，我现在暂时无法回复你的消息，请稍后再试。",
            "error": error
        }


# 测试代码（可选）
async def test_ai_client():
    client = AIClient()
    result = await client.get_ai_response(
        message="你好，介绍一下自己",
        robot_personality="友好的助手",
        conversation_id="test_001"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(test_ai_client())
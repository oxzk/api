"""Telegram Bot API 驱动。"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.exceptions import UpstreamError
from app.core.logging import logger
from app.infrastructure.http.client import HttpClient

TELEGRAM_API_BASE = "https://api.telegram.org/bot"
"""Telegram Bot API 前缀。"""


class TelegramDriver:
    """调用 Telegram Bot API。"""

    def __init__(self, http: HttpClient, token: str, timeout: float = 60.0) -> None:
        """创建驱动。

        Args:
            http: 共享 HTTP 客户端
            token: Bot 访问令牌
            timeout: 请求超时秒数
        """
        self.http = http
        self.token = token
        self.timeout = timeout

    async def call(
        self,
        method: str,
        data: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """调用 Bot API 方法。

        Args:
            method: Telegram 方法名
            data: 表单字段
            files: 上传文件

        Returns:
            Telegram 响应 JSON

        Raises:
            UpstreamError: 上游返回失败或网络异常
        """
        url = f"{TELEGRAM_API_BASE}{self.token}/{method}"
        try:
            response = await self.http.post(
                url,
                data=data,
                files=files,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            logger.error("Telegram 请求异常 method=%s error=%s", method, exc)
            raise UpstreamError("Telegram request failed") from exc

        result = self._read_response(response)
        if not response.is_success or not result.get("ok"):
            logger.error(
                "Telegram 请求失败 method=%s status=%s desc=%s request=%s",
                method,
                response.status_code,
                result.get("description"),
                self._summarize(data, files),
            )
            raise UpstreamError("Telegram request failed")

        return result

    @staticmethod
    def _read_response(response: httpx.Response) -> dict[str, Any]:
        """解析 Telegram 响应。"""
        try:
            payload = response.json()
        except ValueError:
            return {"ok": False, "description": response.text or response.reason_phrase}
        return payload if isinstance(payload, dict) else {"ok": False}

    @staticmethod
    def _summarize(
        data: dict[str, str] | None,
        files: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """序列化请求摘要, 不记录文件内容。"""
        summary: dict[str, Any] = dict(data or {})
        for key, value in (files or {}).items():
            if isinstance(value, tuple) and len(value) >= 2:
                content = value[1]
                summary[key] = {
                    "name": value[0],
                    "type": value[2] if len(value) > 2 else None,
                    "size": len(content) if isinstance(content, (bytes, bytearray)) else None,
                }
            else:
                summary[key] = "<file>"
        return summary


def dump_field(value: Any) -> str:
    """把 dict / list 字段序列化为 JSON 字符串。"""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)

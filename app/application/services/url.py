"""HTTP 代理用例: 校验目标地址并整理回传结果。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse

from app.core.exceptions import BadRequestError
from app.infrastructure.proxy.forward import HttpForwardDriver

ALLOWED_SCHEMES = {"http", "https"}
"""允许代理的协议。"""


@dataclass(slots=True)
class ProxyResult:
    """一次代理转发的结果。"""

    status: int
    content: bytes
    headers: dict[str, str]


class UrlProxyService:
    """通用 HTTP URL 代理。"""

    def __init__(self, forward: HttpForwardDriver) -> None:
        """创建服务。

        Args:
            forward: 转发驱动
        """
        self.forward = forward

    def assert_target_url(self, url: str) -> str:
        """校验目标 URL 为 http(s) 绝对地址。

        Args:
            url: 目标地址

        Returns:
            校验通过的地址
        """
        if not url or not url.strip():
            raise BadRequestError("url required")

        target = url.strip()
        if self._is_absolute(target):
            return target

        # 仅在原值不是绝对 URL 时解码, 避免破坏保留字符
        decoded = unquote(target)
        if decoded != target and self._is_absolute(decoded):
            return decoded

        raise BadRequestError("url must be http or https")

    async def proxy(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> ProxyResult:
        """代理请求到目标 URL。

        Args:
            method: HTTP 方法
            url: 目标地址
            headers: 客户端请求头
            body: 请求体

        Returns:
            代理结果
        """
        target = self.assert_target_url(url)
        status, content, response_headers = await self.forward.forward(
            method.upper(), target, headers, body
        )
        return ProxyResult(status=status, content=content, headers=response_headers)

    async def meta(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> dict[str, Any]:
        """代理请求并返回可读元信息。

        Args:
            method: HTTP 方法
            url: 目标地址
            headers: 客户端请求头
            body: 请求体

        Returns:
            结构化代理结果
        """
        result = await self.proxy(method, url, headers, body)
        content_type = result.headers.get("content-type", result.headers.get("Content-Type", ""))
        try:
            text: str | None = result.content.decode("utf-8")
            is_binary = False
        except UnicodeDecodeError:
            text = None
            is_binary = True

        return {
            "url": self.assert_target_url(url),
            "status": result.status,
            "headers": result.headers,
            "contentType": content_type,
            "size": len(result.content),
            "isBinary": is_binary,
            "body": text,
        }

    @staticmethod
    def _is_absolute(url: str) -> bool:
        """判断是否为受支持的绝对 URL。"""
        try:
            parsed = urlparse(url)
        except ValueError:
            return False
        return parsed.scheme in ALLOWED_SCHEMES and bool(parsed.netloc)

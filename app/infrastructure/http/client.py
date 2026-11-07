"""共享 HTTP 客户端。

由 ApplicationContainer 创建一次并复用, 请求间不保存可变状态。
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any

import httpx

from app.core.exceptions import PayloadTooLargeError, UpstreamError

DEFAULT = httpx.USE_CLIENT_DEFAULT
"""透传 httpx 的客户端默认值, 避免显式 None 关闭超时。"""


class HttpClient:
    """基于 httpx 的异步 HTTP 客户端。"""

    def __init__(self, timeout: float = 30.0, follow_redirects: bool = True) -> None:
        """创建客户端。

        Args:
            timeout: 默认超时秒数
            follow_redirects: 是否自动跟随重定向
        """
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects)

    @property
    def client(self) -> httpx.AsyncClient:
        """底层 httpx 客户端, 仅驱动内部使用。"""
        return self._client

    async def request(
        self,
        method: str,
        url: str,
        *,
        timeout: Any = DEFAULT,
        **kwargs: Any,
    ) -> httpx.Response:
        """发起请求。

        Args:
            method: HTTP 方法
            url: 目标地址
            timeout: 覆盖默认超时, 缺省沿用客户端配置
            **kwargs: 透传给 httpx 的参数

        Returns:
            httpx 响应
        """
        return await self._client.request(method, url, timeout=timeout, **kwargs)

    async def get(self, url: str, *, timeout: Any = DEFAULT, **kwargs: Any) -> httpx.Response:
        """发起 GET 请求。"""
        return await self._client.get(url, timeout=timeout, **kwargs)

    async def post(self, url: str, *, timeout: Any = DEFAULT, **kwargs: Any) -> httpx.Response:
        """发起 POST 请求。"""
        return await self._client.post(url, timeout=timeout, **kwargs)

    def stream(
        self,
        method: str,
        url: str,
        *,
        timeout: Any = DEFAULT,
        **kwargs: Any,
    ) -> AbstractAsyncContextManager[httpx.Response]:
        """以流式方式发起请求, 供需要限制体积的调用方使用。"""
        return self._client.stream(method, url, timeout=timeout, **kwargs)

    async def fetch(self, url: str, *, timeout: float, max_bytes: int) -> bytes:
        """下载完整内容, 超过体积上限立即中断。

        Args:
            url: 目标地址
            timeout: 超时秒数
            max_bytes: 允许的最大字节数

        Returns:
            响应内容

        Raises:
            UpstreamError: 上游返回失败
            PayloadTooLargeError: 响应体超过上限
        """
        async with self.stream("GET", url, timeout=timeout) as response:
            if not response.is_success:
                raise UpstreamError(f"fetch url failed: {response.status_code}")
            return await self.read_limited(response, max_bytes)

    @staticmethod
    async def read_limited(response: httpx.Response, max_bytes: int) -> bytes:
        """流式读取响应体, 超过上限时中断并抛出异常。

        Args:
            response: 已建立的流式响应
            max_bytes: 允许的最大字节数

        Returns:
            完整响应内容
        """
        buffer = bytearray()
        async for chunk in response.aiter_bytes():
            buffer.extend(chunk)
            if len(buffer) > max_bytes:
                raise PayloadTooLargeError(f"response exceeds {max_bytes / (1024 * 1024):g} MB limit")
        return bytes(buffer)

    async def close(self) -> None:
        """关闭底层连接池。"""
        await self._client.aclose()

"""HTTP 转发驱动: 过滤逐跳头并回传上游响应。"""

from __future__ import annotations

from collections.abc import Mapping

import httpx

from app.core.exceptions import UpstreamError, UpstreamTimeoutError
from app.infrastructure.http.client import HttpClient

HOP_BY_HOP_REQUEST_HEADERS = {
    "accept-encoding",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}
"""不允许转发的逐跳请求头。"""

HOP_BY_HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}
"""不允许回传的逐跳响应头。"""


class HttpForwardDriver:
    """把请求原样转发到目标地址。"""

    def __init__(
        self,
        http: HttpClient,
        timeout: float = 30.0,
        max_bytes: int = 20 * 1024 * 1024,
    ) -> None:
        """创建驱动。

        Args:
            http: 共享 HTTP 客户端
            timeout: 上游超时秒数
            max_bytes: 允许回传的最大响应体字节数
        """
        self.http = http
        self.timeout = timeout
        self.max_bytes = max_bytes

    def build_request_headers(self, headers: Mapping[str, str]) -> dict[str, str]:
        """过滤客户端请求头。

        Args:
            headers: 客户端请求头

        Returns:
            可安全转发的请求头
        """
        result: dict[str, str] = {}
        for key, value in headers.items():
            lower = key.lower()
            if lower in HOP_BY_HOP_REQUEST_HEADERS or lower.startswith("x-forwarded-"):
                continue
            result[key] = value
        # httpx 只能可靠解码已安装解码器支持的格式, 禁止上游选择 br/zstd
        result["Accept-Encoding"] = "identity"
        return result

    def build_response_headers(self, headers: httpx.Headers) -> dict[str, str]:
        """过滤上游响应头。

        Args:
            headers: 上游响应头

        Returns:
            可安全回传的响应头
        """
        return {
            key: value
            for key, value in headers.items()
            if key.lower() not in HOP_BY_HOP_RESPONSE_HEADERS
        }

    async def forward(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        """转发请求并按上限读取响应。

        Args:
            method: HTTP 方法
            url: 目标地址
            headers: 客户端请求头
            body: 请求体

        Returns:
            (状态码, 响应体, 响应头)

        Raises:
            UpstreamTimeoutError: 上游超时
            UpstreamError: 其他请求失败
            PayloadTooLargeError: 响应体超过上限
        """
        try:
            async with self.http.stream(
                method,
                url,
                headers=self.build_request_headers(headers),
                content=body,
                timeout=self.timeout,
            ) as response:
                content = await self.http.read_limited(response, self.max_bytes)
                return (
                    response.status_code,
                    content,
                    self.build_response_headers(response.headers),
                )
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("upstream timeout") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(f"upstream request failed: {exc}") from exc

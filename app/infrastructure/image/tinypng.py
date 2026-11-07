"""TinyPNG (tinify) 压缩驱动。"""

from __future__ import annotations

import secrets

import httpx

from app.core.exceptions import (
    AppException,
    PayloadTooLargeError,
    RateLimitError,
    UnsupportedMediaError,
    UpstreamError,
)
from app.infrastructure.http.client import HttpClient

SHRINK_URL = "https://api.tinify.com/shrink"
"""TinyPNG 上传压缩接口。"""

MAX_SOURCE_BYTES = 20 * 1024 * 1024
"""单张图片体积上限 (20 MB)。"""

RESIZE_METHODS = {"fit", "cover", "scale", "thumb"}
"""TinyPNG 支持的缩放方式。"""


class TinypngDriver:
    """调用 TinyPNG API 压缩与缩放图片。"""

    def __init__(
        self,
        http: HttpClient,
        api_keys: list[str],
        timeout: float = 60.0,
    ) -> None:
        """创建驱动。

        Args:
            http: 共享 HTTP 客户端
            api_keys: TinyPNG API Key 列表, 每次请求随机取一个
            timeout: 请求超时秒数
        """
        self.http = http
        self.api_keys = api_keys
        self.timeout = timeout

    async def shrink(self, raw: bytes, auth: httpx.BasicAuth | None = None) -> str:
        """上传图片压缩, 返回压缩结果地址。

        Args:
            raw: 原始图片字节
            auth: 指定本次使用的认证, 缺省时随机取

        Returns:
            TinyPNG 输出图片 URL
        """
        limit_mb = MAX_SOURCE_BYTES // (1024 * 1024)
        if len(raw) > MAX_SOURCE_BYTES:
            raise PayloadTooLargeError(f"image exceeds {limit_mb} MB limit")

        try:
            response = await self.http.post(
                SHRINK_URL,
                content=raw,
                auth=auth or self.pick_auth(),
                headers={"Content-Type": "application/octet-stream"},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"tinypng request failed: {exc}") from exc

        if response.status_code not in {200, 201}:
            raise self.error(response)

        try:
            return str(response.json()["output"]["url"])
        except (ValueError, KeyError, TypeError) as exc:
            raise UpstreamError("invalid tinypng response") from exc

    async def resize(
        self,
        output_url: str,
        width: int | None,
        height: int | None,
        method: str,
        auth: httpx.BasicAuth | None = None,
    ) -> tuple[bytes, str]:
        """在压缩结果上执行缩放。

        Args:
            output_url: 压缩结果地址
            width: 目标宽度
            height: 目标高度
            method: 缩放方式
            auth: 复用压缩请求的认证, 缺省时随机取

        Returns:
            (图片字节, Content-Type)
        """
        if method not in RESIZE_METHODS:
            raise AppException(f"unsupported fit: {method}")
        if method == "scale" and ((width is None) == (height is None)):
            raise AppException("scale requires exactly one of width/height")

        resize: dict[str, int | str] = {"method": method}
        if width:
            resize["width"] = width
        if height:
            resize["height"] = height

        try:
            response = await self.http.post(
                output_url,
                json={"resize": resize},
                auth=auth or self.pick_auth(),
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"tinypng resize failed: {exc}") from exc

        if response.status_code not in {200, 201}:
            raise self.error(response)

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                next_url = str(response.json()["output"]["url"])
            except (ValueError, KeyError, TypeError) as exc:
                raise UpstreamError("invalid tinypng response") from exc
            return await self.download(next_url, auth)

        return response.content, content_type or "application/octet-stream"

    async def download(
        self,
        output_url: str,
        auth: httpx.BasicAuth | None = None,
    ) -> tuple[bytes, str]:
        """下载压缩结果。

        Args:
            output_url: 压缩结果地址
            auth: 复用压缩请求的认证, 缺省时随机取

        Returns:
            (图片字节, Content-Type)
        """
        try:
            response = await self.http.get(
                output_url,
                auth=auth or self.pick_auth(),
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"tinypng download failed: {exc}") from exc

        if not response.is_success:
            raise self.error(response)
        return response.content, response.headers.get("content-type", "application/octet-stream")

    def pick_auth(self) -> httpx.BasicAuth:
        """随机选择一个 API Key 构造认证。

        Returns:
            BasicAuth 实例, 用户名为 api
        """
        if not self.api_keys:
            raise AppException("tinypng api key not configured", status_code=500)
        return httpx.BasicAuth("api", secrets.choice(self.api_keys))

    def error(self, response: httpx.Response) -> AppException:
        """把 TinyPNG 错误响应转换为业务异常。

        Args:
            response: TinyPNG 响应

        Returns:
            对应状态码的业务异常
        """
        message = ""
        try:
            payload = response.json()
            message = str(payload.get("message") or payload.get("error") or "")
        except (ValueError, AttributeError):
            message = response.text[:200]

        if response.status_code == 401:
            return AppException(message or "invalid tinypng api key", status_code=401)
        if response.status_code == 413:
            return PayloadTooLargeError("image too large for tinypng")
        if response.status_code == 415:
            return UnsupportedMediaError("unsupported image type")
        if response.status_code == 429:
            return RateLimitError("tinypng rate limit exceeded")
        return UpstreamError(message or "tinypng request failed")

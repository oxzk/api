"""远程内容 Base58 编解码用例。"""

from __future__ import annotations

from app.core.algorithms import base58
from app.core.exceptions import BadRequestError
from app.infrastructure.http.client import HttpClient

MAX_SOURCE_BYTES = 20 * 1024 * 1024
"""远程内容体积上限 (20 MB)。"""


class EncodingService:
    """拉取远程内容并执行 Base58 编解码。"""

    def __init__(
        self,
        http: HttpClient,
        timeout: float = 30.0,
        max_bytes: int = MAX_SOURCE_BYTES,
    ) -> None:
        """创建服务。

        Args:
            http: 共享 HTTP 客户端
            timeout: 远程请求超时秒数
            max_bytes: 允许拉取的最大字节数
        """
        self.http = http
        self.timeout = timeout
        self.max_bytes = max_bytes

    async def encode_url(self, url: str) -> str:
        """拉取远程内容并编码为 Base58。

        Args:
            url: 远程内容地址

        Returns:
            Base58 编码结果
        """
        return base58.encode(await self.fetch(url))

    async def decode_url(self, url: str) -> str:
        """拉取远程 Base58 内容并解码为文本。

        Args:
            url: 远程 Base58 文本地址

        Returns:
            UTF-8 或 Latin-1 解码结果
        """
        content = await self.fetch(url)
        try:
            encoded = content.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise BadRequestError("invalid base58") from exc

        raw = base58.decode(encoded)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")

    async def fetch(self, url: str) -> bytes:
        """拉取远程内容。

        Args:
            url: 远程地址

        Returns:
            响应二进制内容
        """
        if not url or not url.strip():
            raise BadRequestError("url required")
        return await self.http.fetch(url, timeout=self.timeout, max_bytes=self.max_bytes)

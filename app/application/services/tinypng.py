"""图片压缩用例: 读取三种输入源后交给 TinyPNG。"""

from __future__ import annotations

import base64
import binascii

from app.core.exceptions import BadRequestError, UnsupportedMediaError
from app.infrastructure.http.client import HttpClient
from app.infrastructure.image.tinypng import TinypngDriver

IMAGE_MAGIC = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"BM",
)
"""常见图片文件头。"""


class TinypngService:
    """读取图片并压缩, 可选缩放。"""

    def __init__(
        self,
        http: HttpClient,
        driver: TinypngDriver,
        timeout: float = 30.0,
        max_bytes: int = 20 * 1024 * 1024,
    ) -> None:
        """创建服务。

        Args:
            http: 共享 HTTP 客户端
            driver: TinyPNG 驱动
            timeout: 源图下载超时秒数
            max_bytes: 允许下载的最大字节数
        """
        self.http = http
        self.driver = driver
        self.timeout = timeout
        self.max_bytes = max_bytes

    async def compress(
        self,
        source: str | bytes,
        *,
        width: int | None = None,
        height: int | None = None,
        fit: str = "fit",
    ) -> tuple[bytes, str]:
        """压缩图片, 可选缩放。

        Args:
            source: 图片 URL、Base64 / Data URI 字符串, 或原始图片字节
            width: 目标宽度
            height: 目标高度
            fit: 缩放方式 (fit/cover/scale/thumb)

        Returns:
            (图片字节, Content-Type)
        """
        raw = await self.load(source)
        auth = self.driver.pick_auth()
        output_url = await self.driver.shrink(raw, auth)
        if width or height:
            return await self.driver.resize(output_url, width, height, fit.lower(), auth)
        return await self.driver.download(output_url, auth)

    async def load(self, source: str | bytes) -> bytes:
        """把三种输入形式统一解析为图片字节。

        Args:
            source: URL、Base64 / Data URI 字符串, 或原始图片字节

        Returns:
            图片字节
        """
        if isinstance(source, (bytes, bytearray)):
            raw = bytes(source)
            if not raw:
                raise BadRequestError("source required")
            if not self.looks_like_image(raw):
                raise UnsupportedMediaError("source is not a supported image")
            return raw

        value = (source or "").strip()
        if not value:
            raise BadRequestError("source required")

        if value.lower().startswith(("http://", "https://")):
            return await self.fetch(value)

        if value.lower().startswith("data:"):
            _, _, value = value.partition(",")
            value = value.strip()

        return self.decode_base64(value)

    async def fetch(self, url: str) -> bytes:
        """下载远程图片。

        Args:
            url: 源图地址

        Returns:
            图片字节
        """
        return await self.http.fetch(url, timeout=self.timeout, max_bytes=self.max_bytes)

    def decode_base64(self, value: str) -> bytes:
        """解码 Base64 图片数据。

        兼容查询串中 ``+`` 被解码成空格、URL-safe 字母表与省略填充。

        Args:
            value: Base64 字符串

        Returns:
            图片字节
        """
        candidates = ["".join(value.split()), value.replace(" ", "+").strip()]
        last_error: Exception | None = None
        for candidate in candidates:
            normalized = candidate.replace("-", "+").replace("_", "/")
            padding = "=" * (-len(normalized) % 4)
            try:
                raw = base64.b64decode(normalized + padding, validate=True)
            except (binascii.Error, ValueError) as exc:
                last_error = exc
                continue

            if not raw:
                raise BadRequestError("empty image data")
            if not self.looks_like_image(raw):
                raise UnsupportedMediaError("source is not a supported image")
            return raw

        raise BadRequestError("invalid base64 source") from last_error

    @staticmethod
    def looks_like_image(raw: bytes) -> bool:
        """按文件头判断是否为常见图片格式。

        Args:
            raw: 图片字节

        Returns:
            是否命中已知图片文件头
        """
        if raw.startswith(IMAGE_MAGIC):
            return True
        if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            return True
        if raw[4:8] == b"ftyp":
            return raw[8:12] in {b"avif", b"avis", b"heic", b"heix", b"mif1", b"msf1"}
        return False

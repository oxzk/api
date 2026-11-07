"""Telegram 消息发送用例。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import BadRequestError, ConfigurationError
from app.infrastructure.notification.telegram import TelegramDriver


@dataclass(slots=True)
class Upload:
    """已读入内存的上传文件。"""

    filename: str
    content: bytes
    content_type: str


class NotificationService:
    """把请求参数整理为 Telegram API 调用。"""

    def __init__(self, driver: TelegramDriver, default_chat_id: str) -> None:
        """创建服务。

        Args:
            driver: Telegram 驱动
            default_chat_id: 默认会话 ID
        """
        self.driver = driver
        self.default_chat_id = default_chat_id

    async def send_text(self, params: dict[str, Any]) -> dict[str, Any]:
        """发送文本消息。

        Args:
            params: 原始请求参数, 按字段名原样转发

        Returns:
            Telegram 响应
        """
        self.ensure_configured()
        data = self._form_fields(params)
        self._ensure_chat_id(data)
        return await self.driver.call("sendMessage", data=data)

    async def send_image(
        self,
        upload: Upload | None = None,
        photo: str | None = None,
        caption: str = "",
        chat_id: str | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """发送单张图片。

        Args:
            upload: 上传的图片文件
            photo: 图片远程地址或文件 ID
            caption: 图片说明
            chat_id: 目标会话 ID
            parse_mode: 文本解析模式

        Returns:
            Telegram 响应
        """
        self.ensure_configured()
        if upload is None and not photo:
            raise BadRequestError("photo required")

        data: dict[str, str] = {
            "chat_id": chat_id or self.default_chat_id,
            "caption": caption,
            "parse_mode": parse_mode,
        }
        files: dict[str, Any] | None = None
        if upload is not None:
            files = {
                "photo": (upload.filename or "photo.jpg", upload.content, upload.content_type)
            }
        elif photo:
            data["photo"] = photo

        return await self.driver.call("sendPhoto", data=data, files=files)

    async def send_images(
        self,
        uploads: list[Upload],
        caption: str = "",
        chat_id: str | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """发送多张图片。

        Args:
            uploads: 上传的图片文件列表
            caption: 首张图片说明
            chat_id: 目标会话 ID
            parse_mode: 文本解析模式

        Returns:
            Telegram 响应
        """
        self.ensure_configured()
        if not uploads:
            raise BadRequestError("media required")

        media: list[dict[str, str]] = [
            {"type": "photo", "media": f"attach://photo{index}"} for index in range(len(uploads))
        ]
        if caption:
            media[0] = {**media[0], "caption": caption, "parse_mode": parse_mode}

        files: dict[str, Any] = {}
        for index, upload in enumerate(uploads):
            files[f"photo{index}"] = (
                upload.filename or f"photo{index}.jpg",
                upload.content,
                upload.content_type,
            )

        data = {
            "chat_id": chat_id or self.default_chat_id,
            "media": json.dumps(media),
        }
        return await self.driver.call("sendMediaGroup", data=data, files=files)

    async def send_document(
        self,
        upload: Upload | None = None,
        document: str | None = None,
        caption: str = "",
        chat_id: str | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """发送文档。

        Args:
            upload: 上传的文档文件
            document: 文档远程地址或文件 ID
            caption: 文档说明
            chat_id: 目标会话 ID
            parse_mode: 文本解析模式

        Returns:
            Telegram 响应
        """
        self.ensure_configured()
        if upload is None and not document:
            raise BadRequestError("document required")

        data: dict[str, str] = {
            "chat_id": chat_id or self.default_chat_id,
            "caption": caption,
            "parse_mode": parse_mode,
        }
        files: dict[str, Any] | None = None
        if upload is not None:
            files = {
                "document": (
                    upload.filename or "document.bin",
                    upload.content,
                    upload.content_type,
                )
            }
        elif document:
            data["document"] = document

        return await self.driver.call("sendDocument", data=data, files=files)

    def ensure_configured(self) -> None:
        """确认 Bot Token 与默认会话已配置。

        Raises:
            ConfigurationError: 缺少必要配置
        """
        if not self.driver.token:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN required")
        if not self.default_chat_id:
            raise ConfigurationError("TELEGRAM_CHAT_ID required")

    def _ensure_chat_id(self, data: dict[str, str]) -> None:
        """请求未带 chat_id 时补充默认会话。"""
        chat_id = data.get("chat_id", "")
        if not chat_id.strip():
            data["chat_id"] = self.default_chat_id

    @staticmethod
    def _form_fields(params: dict[str, Any]) -> dict[str, str]:
        """把请求参数转换为表单字段。"""
        data: dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            data[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        return data

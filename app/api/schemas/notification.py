"""通知类接口的请求结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramTextPayload(BaseModel):
    """Telegram 文本消息请求体。"""

    text: str = Field(description="消息文本内容")
    chat_id: str | None = Field(default=None, description="目标会话 ID")
    parse_mode: str | None = Field(default=None, description="文本解析模式")

    model_config = {"extra": "allow"}

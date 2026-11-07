"""编解码类接口的请求结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DataPayload(BaseModel):
    """单字段 data 请求体。"""

    data: str = Field(description="待处理字符串")

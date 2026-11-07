"""基础接口的响应结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GetEchoData(BaseModel):
    """/get 回显数据。"""

    args: dict[str, str] = Field(default_factory=dict, description="查询参数")
    headers: dict[str, str] = Field(default_factory=dict, description="请求头")
    origin: str = Field(description="客户端来源")
    url: str = Field(description="完整请求 URL")

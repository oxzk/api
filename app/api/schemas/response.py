"""统一响应信封, 保持历史字段与语义。"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应。

    路由可直接返回业务 data, 由 model_validator 包装为成功响应。
    """

    code: int = Field(default=0, description="业务状态码, 0 表示成功")
    message: str = Field(default="ok", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @model_validator(mode="before")
    @classmethod
    def wrap_success_response(cls, value: object) -> object:
        """将裸返回数据包装为成功响应。"""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict) and {"code", "data"} <= set(value):
            return value
        return {"code": 0, "message": "ok", "data": value}

    @classmethod
    def fail(cls, message: str, code: int = 400, data: T | None = None) -> APIResponse[T]:
        """构造失败响应。

        Args:
            message: 错误信息
            code: 业务/HTTP 状态码
            data: 可选附加数据
        """
        return cls(code=code, message=message, data=data)


class ResultData(BaseModel):
    """单字段 result 响应数据。"""

    result: str = Field(description="处理结果")

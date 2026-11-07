"""基础 API 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.api.schemas.base import GetEchoData
from app.api.schemas.response import APIResponse

router = APIRouter(tags=["base"])


@router.get("/", response_model=APIResponse[dict[str, Any]])
async def root() -> Any:
    """返回 API 根路径响应。"""
    return {}


@router.get("/get", response_model=APIResponse[GetEchoData])
async def httpbin_get(request: Request) -> Any:
    """返回 GET 请求信息, 语义与 httpbin.org/get 一致。"""
    origin = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for")
        or (request.client.host if request.client else "unknown")
    )
    return {
        "args": dict(request.query_params),
        "headers": dict(request.headers.items()),
        "origin": origin,
        "url": str(request.url),
    }

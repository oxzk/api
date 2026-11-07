"""URL 编解码与 HTTP 代理路由。"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, unquote

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.api.dependencies import Container
from app.api.schemas.encoding import DataPayload
from app.api.schemas.response import APIResponse, ResultData
from app.core.exceptions import BadRequestError

router = APIRouter(prefix="/url", tags=["url"])

FORWARD_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
"""需要携带请求体的方法。"""


@router.post("/encode", response_model=APIResponse[ResultData])
async def encode(payload: DataPayload) -> Any:
    """URL 编码 (encodeURIComponent 语义)。"""
    if not payload.data:
        raise BadRequestError("data required")
    return {"result": quote(payload.data, safe="")}


@router.post("/decode", response_model=APIResponse[ResultData])
async def decode(payload: DataPayload) -> Any:
    """URL 解码。"""
    if not payload.data:
        raise BadRequestError("data required")
    return {"result": unquote(payload.data)}


@router.get("/proxy")
@router.post("/proxy")
async def proxy(
    request: Request,
    container: Container,
    url: str = Query(..., description="目标 URL (http/https)"),
    method: str | None = Query(default=None, description="可选覆盖 HTTP 方法"),
) -> Response:
    """HTTP 代理: 转发请求到目标 URL, 原样回传状态码与正文。"""
    http_method = (method or request.method).upper()
    body = await request.body() if http_method in FORWARD_METHODS else None
    result = await container.urls.proxy(http_method, url, request.headers, body or None)
    return Response(content=result.content, status_code=result.status, headers=result.headers)


@router.get("/proxy/meta", response_model=APIResponse[dict[str, Any]])
async def proxy_meta(
    request: Request,
    container: Container,
    url: str = Query(..., description="目标 URL (http/https)"),
) -> Any:
    """HTTP 代理元信息: 返回状态码、响应头与文本正文。"""
    http_method = request.method.upper()
    body = await request.body() if http_method in FORWARD_METHODS else None
    return await container.urls.meta(http_method, url, request.headers, body or None)

"""图片压缩路由。

通过 TinyPNG API 压缩图片, 支持 URL / Base64 / 二进制输入, 可选在线缩放。
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.api.dependencies import Container
from app.core.exceptions import BadRequestError

router = APIRouter(prefix="/tinypng", tags=["tinypng"])


@router.get("")
async def compress_image(
    container: Container,
    url: str = Query(..., description="图片 URL、Base64 或 data URI"),
    width: int | None = Query(default=None, description="目标宽度"),
    height: int | None = Query(default=None, description="目标高度"),
    fit: str = Query(default="fit", description="缩放方式: fit/cover/scale/thumb"),
) -> Response:
    """压缩 URL / Base64 来源的图片。"""
    content, content_type = await container.tinypng.compress(
        url,
        width=width,
        height=height,
        fit=fit,
    )
    return Response(content=content, media_type=content_type)


@router.post("")
async def compress_image_body(
    request: Request,
    container: Container,
    width: int | None = Query(default=None, description="目标宽度"),
    height: int | None = Query(default=None, description="目标高度"),
    fit: str = Query(default="fit", description="缩放方式: fit/cover/scale/thumb"),
) -> Response:
    """压缩二进制上传的图片。

    支持三种请求体: 原始二进制 (Content-Type: image/*)、
    JSON ``{"data": "<url|base64>"}``、multipart 表单字段 ``file``。
    """
    content_type = request.headers.get("content-type", "").lower()

    if content_type.startswith("application/json"):
        try:
            payload = await request.json()
        except ValueError as exc:
            raise BadRequestError("invalid json body") from exc
        if not isinstance(payload, dict):
            raise BadRequestError("json object required")
        source = payload.get("data") or payload.get("url") or payload.get("source")
        if not isinstance(source, str) or not source.strip():
            raise BadRequestError("data required")
    elif content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise BadRequestError("file field required")
        source = await upload.read()
    else:
        source = await request.body()
        if not source:
            raise BadRequestError("image body required")

    content, media_type = await container.tinypng.compress(
        source,
        width=width,
        height=height,
        fit=fit,
    )
    return Response(content=content, media_type=media_type)

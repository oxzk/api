"""Telegram 消息发送路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, UploadFile

from app.api.dependencies import Container
from app.api.schemas.notification import TelegramTextPayload
from app.api.schemas.response import APIResponse
from app.application.services.notification import Upload

router = APIRouter(prefix="/tg", tags=["telegram"])


async def to_upload(file: UploadFile | None) -> Upload | None:
    """把上传对象读入内存。

    Args:
        file: FastAPI 上传对象

    Returns:
        应用层上传结构, 无文件时返回 None
    """
    if file is None:
        return None
    return Upload(
        filename=file.filename or "",
        content=await file.read(),
        content_type=file.content_type or "application/octet-stream",
    )


@router.post("/text", response_model=APIResponse[Any])
async def send_text(
    payload: TelegramTextPayload,
    container: Container,
) -> Any:
    """发送文本消息。"""
    return await container.notifications.send_text(payload.model_dump(exclude_none=True))


@router.post("/image", response_model=APIResponse[Any])
async def send_image(
    container: Container,
    file: UploadFile | None = File(default=None),
    photo: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    caption: str = Form(default=""),
    chat_id: str | None = Form(default=None),
    parse_mode: str = Form(default="HTML"),
) -> Any:
    """发送单张图片。"""
    upload = await to_upload(file or image)
    return await container.notifications.send_image(
        upload,
        photo if isinstance(photo, str) else None,
        caption,
        chat_id,
        parse_mode,
    )


@router.post("/images", response_model=APIResponse[Any])
async def send_images(
    container: Container,
    file: UploadFile | None = File(default=None),
    photo: UploadFile | None = File(default=None),
    image: UploadFile | None = File(default=None),
    caption: str = Form(default=""),
    chat_id: str | None = Form(default=None),
    parse_mode: str = Form(default="HTML"),
) -> Any:
    """发送多张图片。"""
    uploads = [
        upload
        for upload in [await to_upload(item) for item in (file, photo, image)]
        if upload is not None
    ]
    return await container.notifications.send_images(uploads, caption, chat_id, parse_mode)


@router.post("/document", response_model=APIResponse[Any])
async def send_document(
    container: Container,
    file: UploadFile | None = File(default=None),
    document: str | None = Form(default=None),
    caption: str = Form(default=""),
    chat_id: str | None = Form(default=None),
    parse_mode: str = Form(default="HTML"),
) -> Any:
    """发送文档。"""
    upload = await to_upload(file)
    return await container.notifications.send_document(
        upload,
        document if isinstance(document, str) else None,
        caption,
        chat_id,
        parse_mode,
    )

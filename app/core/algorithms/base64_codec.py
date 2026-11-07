"""Base64 文本编解码, 语义对齐 Workers 的 btoa / atob。"""

from __future__ import annotations

import base64
import binascii

from app.core.exceptions import BadRequestError


def encode_text(text: str) -> str:
    """编码文本。

    与 Workers ``btoa`` 对齐: 优先按 Latin-1 字节处理, 非 Latin-1 回退 UTF-8。

    Args:
        text: 待编码文本

    Returns:
        Base64 字符串

    Raises:
        BadRequestError: 文本为空
    """
    if not text:
        raise BadRequestError("data required")

    try:
        raw = text.encode("latin-1")
    except UnicodeEncodeError:
        raw = text.encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode_text(text: str) -> str:
    """解码 Base64 文本。

    Args:
        text: Base64 字符串

    Returns:
        解码后的文本, 优先 UTF-8, 失败回退 Latin-1

    Raises:
        BadRequestError: 文本为空或不是合法 Base64
    """
    if not text:
        raise BadRequestError("data required")

    try:
        raw = base64.b64decode(text)
    except (binascii.Error, ValueError) as exc:
        raise BadRequestError("invalid base64") from exc

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")

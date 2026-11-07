"""Base58 编解码 (Bitcoin 字母表)。"""

from __future__ import annotations

from app.core.exceptions import BadRequestError

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
"""Base58 字母表, 排除 0OIl。"""

BASE58_INDEX = {character: index for index, character in enumerate(BASE58_ALPHABET)}
"""字符到数值的索引。"""


def encode(data: bytes) -> str:
    """将二进制数据编码为 Base58 字符串。

    Args:
        data: 待编码二进制数据

    Returns:
        Base58 编码结果
    """
    if not data:
        return ""

    zero_count = len(data) - len(data.lstrip(b"\0"))
    value = int.from_bytes(data, "big")
    encoded: list[str] = []
    while value > 0:
        value, remainder = divmod(value, 58)
        encoded.append(BASE58_ALPHABET[remainder])

    return "1" * zero_count + "".join(reversed(encoded))


def decode(text: str) -> bytes:
    """将 Base58 字符串解码为二进制数据。

    Args:
        text: 待解码 Base58 字符串

    Returns:
        解码后的二进制数据

    Raises:
        BadRequestError: 含非法字符
    """
    if not text:
        return b""

    zero_count = len(text) - len(text.lstrip("1"))
    value = 0
    try:
        for character in text:
            value = value * 58 + BASE58_INDEX[character]
    except KeyError as exc:
        raise BadRequestError("invalid base58") from exc

    byte_count = (value.bit_length() + 7) // 8
    return b"\0" * zero_count + value.to_bytes(byte_count, "big")

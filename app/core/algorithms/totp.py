"""TOTP (RFC 6238) 两步验证算法, 基于标准库实现。"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse
from collections.abc import Callable

from app.core.exceptions import BadRequestError

DEFAULT_PERIOD = 30
"""默认时间步长 (秒)。"""

DEFAULT_DIGITS = 6
"""默认验证码位数。"""

DEFAULT_SECRET_BYTES = 20
"""默认密钥字节数 (160 bit)。"""

SUPPORTED_ALGORITHMS: dict[str, Callable[..., object]] = {
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}
"""支持的 HMAC 哈希算法。"""


def generate_secret(length: int = DEFAULT_SECRET_BYTES) -> str:
    """生成 Base32 随机密钥。

    Args:
        length: 原始随机字节数

    Returns:
        Base32 编码密钥 (无填充)
    """
    return base64.b32encode(secrets.token_bytes(length)).decode("ascii").rstrip("=")


def hotp(
    secret: str,
    counter: int,
    digits: int = DEFAULT_DIGITS,
    algorithm: str = "sha1",
) -> str:
    """计算 HOTP (RFC 4226) 验证码。

    Args:
        secret: Base32 编码密钥
        counter: 计数器
        digits: 验证码位数
        algorithm: HMAC 哈希算法名称

    Returns:
        定长数字验证码
    """
    key = _decode_secret(secret)
    digest_mod = SUPPORTED_ALGORITHMS.get(algorithm.lower())
    if digest_mod is None:
        raise BadRequestError(f"unsupported algorithm: {algorithm}")

    digest = hmac.new(key, struct.pack(">Q", counter), digest_mod).digest()  # type: ignore[arg-type]
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def totp(
    secret: str,
    timestamp: int | None = None,
    period: int = DEFAULT_PERIOD,
    digits: int = DEFAULT_DIGITS,
    algorithm: str = "sha1",
) -> str:
    """计算当前时间窗口的 TOTP 验证码。

    Args:
        secret: Base32 编码密钥
        timestamp: Unix 时间戳, 默认当前时间
        period: 时间步长 (秒)
        digits: 验证码位数
        algorithm: HMAC 哈希算法名称

    Returns:
        当前 TOTP 验证码
    """
    if period <= 0:
        raise BadRequestError("period must be positive")
    moment = int(time.time()) if timestamp is None else timestamp
    return hotp(secret, moment // period, digits=digits, algorithm=algorithm)


def verify(
    secret: str,
    code: str,
    window: int = 1,
    period: int = DEFAULT_PERIOD,
    digits: int = DEFAULT_DIGITS,
    algorithm: str = "sha1",
) -> bool:
    """校验验证码, 允许前后 ``window`` 个时间窗口的时钟偏移。

    Args:
        secret: Base32 编码密钥
        code: 待校验验证码
        window: 允许的时钟偏移窗口数
        period: 时间步长 (秒)
        digits: 验证码位数
        algorithm: HMAC 哈希算法名称

    Returns:
        校验是否通过
    """
    normalized = (code or "").strip().replace(" ", "")
    if len(normalized) != digits or not normalized.isdigit():
        return False

    _decode_secret(secret)
    current = int(time.time()) // period
    for offset in range(-window, window + 1):
        expected = hotp(secret, current + offset, digits=digits, algorithm=algorithm)
        if hmac.compare_digest(expected, normalized):
            return True
    return False


def build_uri(
    secret: str,
    account: str,
    issuer: str = "API",
    period: int = DEFAULT_PERIOD,
    digits: int = DEFAULT_DIGITS,
    algorithm: str = "sha1",
) -> str:
    """构造 otpauth:// URI, 供验证器 App 扫码导入。

    Args:
        secret: Base32 编码密钥
        account: 账户标识
        issuer: 发行方名称
        period: 时间步长 (秒)
        digits: 验证码位数
        algorithm: HMAC 哈希算法名称

    Returns:
        otpauth://totp/... URI
    """
    if not account or not account.strip():
        raise BadRequestError("account required")

    label = urllib.parse.quote(f"{issuer}:{account}", safe=":")
    params = urllib.parse.urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "period": period,
            "digits": digits,
            "algorithm": algorithm.upper(),
        }
    )
    return f"otpauth://totp/{label}?{params}"


def _decode_secret(secret: str) -> bytes:
    """解码 Base32 密钥。

    Args:
        secret: Base32 编码密钥

    Returns:
        原始密钥字节

    Raises:
        BadRequestError: 密钥为空或格式非法
    """
    normalized = (secret or "").strip().replace(" ", "").upper()
    if not normalized:
        raise BadRequestError("secret required")

    padding = "=" * (-len(normalized) % 8)
    try:
        return base64.b32decode(normalized + padding, casefold=True)
    except (binascii.Error, ValueError) as exc:
        raise BadRequestError("invalid secret: not valid base32") from exc

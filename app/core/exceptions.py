"""统一业务异常及稳定错误码。"""

from __future__ import annotations

from typing import Any, NoReturn


class AppException(Exception):
    """携带可公开错误信息的业务异常。

    ``code`` 用于日志与监控归类, 不进入响应体; 响应体保持历史包络。
    """

    code = "application_error"
    status_code = 400

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """记录可安全返回给客户端的错误信息。"""
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class BadRequestError(AppException):
    """请求内容不合法。"""

    code = "bad_request"
    status_code = 400


class NotFoundError(AppException):
    """请求的资源不存在。"""

    code = "not_found"
    status_code = 404


class PayloadTooLargeError(AppException):
    """请求体超过上游限制。"""

    code = "payload_too_large"
    status_code = 413


class UnsupportedMediaError(AppException):
    """不支持的媒体类型。"""

    code = "unsupported_media"
    status_code = 415


class RateLimitError(AppException):
    """上游限流。"""

    code = "rate_limited"
    status_code = 429


class UpstreamError(AppException):
    """上游服务返回异常。"""

    code = "upstream_error"
    status_code = 502


class UpstreamTimeoutError(AppException):
    """上游服务超时。"""

    code = "upstream_timeout"
    status_code = 504


class ConfigurationError(AppException):
    """必要配置缺失或无效。"""

    code = "configuration_error"
    status_code = 500


def fail(message: str, status_code: int = 400) -> NoReturn:
    """抛出业务异常, 由统一异常边界生成响应。

    Args:
        message: 客户端可见错误信息
        status_code: HTTP 状态码
    """
    raise AppException(message, status_code=status_code)

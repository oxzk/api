"""统一异常边界: 业务异常, 参数校验, HTTP 异常与未知错误。"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.response import APIResponse
from app.core.exceptions import AppException
from app.core.logging import logger


def error_response(
    status_code: int,
    message: str,
    data: object | None = None,
) -> JSONResponse:
    """构造统一错误响应。

    Args:
        status_code: HTTP 状态码
        message: 错误信息
        data: 可选附加数据
    """
    return JSONResponse(
        status_code=status_code,
        content=APIResponse.fail(message=message, code=status_code, data=data).model_dump(
            mode="json"
        ),
    )


def format_validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    """格式化请求参数校验错误。

    Args:
        exc: 校验异常

    Returns:
        字段与错误信息列表
    """
    formatted: list[dict[str, str]] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        formatted.append({"field": location, "message": str(error.get("msg") or "参数无效")})
    return formatted


def register_exception_handlers(application: FastAPI) -> None:
    """注册全部异常处理器。

    Args:
        application: FastAPI 应用
    """

    @application.exception_handler(AppException)
    async def handle_app_error(request: Request, exc: AppException) -> JSONResponse:
        """处理业务异常。"""
        logger.warning(
            "业务异常 %s %s code=%s status=%s message=%s",
            request.method,
            request.url.path,
            exc.code,
            exc.status_code,
            exc.message,
        )
        return error_response(exc.status_code, exc.message)

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """处理请求参数校验异常。"""
        return error_response(422, "请求参数无效", data={"errors": format_validation_errors(exc)})

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """处理 HTTP 异常。"""
        if exc.status_code == 404:
            return error_response(404, "Not found")
        return error_response(exc.status_code, str(exc.detail) if exc.detail else "请求失败")

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """处理未预期异常, 记录完整调用栈。"""
        logger.exception(
            "未处理异常: %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return error_response(500, "Internal server error")

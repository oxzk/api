"""请求上下文中间件: 追踪标识, 响应头回写与访问日志。"""

from __future__ import annotations

import re
import time
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import logger

REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")
"""可信任的请求标识格式。"""


class RequestContextMiddleware:
    """为请求分配追踪标识, 并记录状态码与耗时。"""

    def __init__(self, app: ASGIApp) -> None:
        """保存下游 ASGI 应用。"""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """写入 request_id, 并在响应开始时回写响应头。"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = Headers(scope=scope).get("x-request-id", "")
        request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        started = time.perf_counter()
        status = 500

        async def send_with_context(message: Message) -> None:
            """在响应发送前补充追踪标识。"""
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)["x-request-id"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "%s %s -> %s %.2fms request_id=%s",
                scope.get("method", ""),
                scope.get("path", ""),
                status,
                elapsed_ms,
                request_id,
            )

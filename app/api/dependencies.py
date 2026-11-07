"""HTTP 依赖: 读取 lifespan 组装好的容器。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.application.container import ApplicationContainer


async def get_container(request: Request) -> ApplicationContainer:
    """读取容器, 未经过 lifespan 时在锁内惰性创建一次。

    Vercel 等运行时对 ASGI lifespan 支持不完整, 这里做兜底: 用应用级锁保证
    并发首请求只创建一个容器, 避免重复建连接池。

    Args:
        request: 当前请求

    Returns:
        应用容器
    """
    container: ApplicationContainer | None = getattr(request.app.state, "container", None)
    if container is not None:
        return container

    async with request.app.state.container_lock:
        container = getattr(request.app.state, "container", None)
        if container is None:
            container = await ApplicationContainer.create()
            request.app.state.container = container
        return container


Container = Annotated[ApplicationContainer, Depends(get_container)]
"""路由使用的容器依赖。"""

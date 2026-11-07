"""FastAPI 应用入口, 只负责生命周期与 HTTP 边界组装。"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestContextMiddleware
from app.api.v1.routes import router
from app.application.container import ApplicationContainer
from app.core.config import Settings
from app.core.logging import logger


def create_app(settings: Settings | None = None) -> FastAPI:
    """构建应用, 有副作用的初始化全部留在 lifespan。

    Args:
        settings: 外部注入的配置, 缺省从环境加载

    Returns:
        组装完成的 FastAPI 应用
    """

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        """启动时组装容器, 退出时释放共享资源。"""
        if getattr(application.state, "container", None) is None:
            application.state.container = await ApplicationContainer.create(settings)
        try:
            yield
        finally:
            container: ApplicationContainer | None = getattr(
                application.state, "container", None
            )
            if container is not None:
                await container.shutdown()

    application = FastAPI(
        title="API",
        version="1.0.0",
        description="通用工具 API",
        docs_url=None,
        redoc_url="/docs",
        redirect_slashes=False,
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    # 无 Cookie / 凭证鉴权, 通配来源与 allow_credentials 不能同时开启
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )
    application.state.container_lock = asyncio.Lock()
    register_exception_handlers(application)
    # 同一套路由同时挂到带版本前缀与裸路径, 两种调用方式等价
    application.include_router(router, prefix="/v1")
    application.include_router(router)
    return application


app = create_app()
"""模块级应用实例, Vercel 入口依赖它。"""

logger.info("API application ready")

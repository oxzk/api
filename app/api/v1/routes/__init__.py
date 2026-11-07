"""统一路由注册, 由 main 挂载到 /v1 前缀。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    base,
    codec,
    fake,
    health,
    oauth,
    tg,
    tinypng,
    totp,
    url,
)

router = APIRouter()

for module in (health, base, codec, url, tinypng, oauth, tg, totp, fake):
    router.include_router(module.router)

__all__ = ["router"]

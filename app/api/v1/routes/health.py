"""公开健康检查。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.schemas.response import APIResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=APIResponse[dict[str, Any]])
async def health() -> Any:
    """返回健康检查响应。"""
    return {}

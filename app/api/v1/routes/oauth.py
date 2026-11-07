"""OAuth redirect_uri 中转路由。

向提供商注册固定 redirect_uri = {origin}/v1/oauth/callback
将真实回调地址与业务 state 写入 OAuth state, 回调后 302 转发 code 等参数。
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import Container
from app.core.exceptions import BadRequestError

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/callback")
async def oauth_callback(request: Request, container: Container) -> RedirectResponse:
    """OAuth 回调中转: 解析 state 中的真实 redirect, 转发 code 等参数并 302。"""
    params = container.oauth.normalize_params(dict(request.query_params))
    state = params.get("state")
    if not state:
        raise BadRequestError("state required")

    relay = container.oauth.parse_state(state)
    return RedirectResponse(url=container.oauth.build_target_url(relay, params), status_code=302)

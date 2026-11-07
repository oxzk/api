"""TOTP (2FA) 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.api.schemas.response import APIResponse, ResultData
from app.api.schemas.totp import (
    TotpSetupData,
    TotpSetupPayload,
    TotpVerifyData,
    TotpVerifyPayload,
)
from app.core.algorithms import totp

router = APIRouter(tags=["2fa"])


@router.get("/2fa", response_model=APIResponse[ResultData])
async def code(
    secret: str = Query(..., description="Base32 编码密钥"),
    period: int = Query(default=30, ge=1, le=300, description="时间步长 (秒)"),
    digits: int = Query(default=6, ge=6, le=8, description="验证码位数"),
    algorithm: str = Query(default="sha1", description="HMAC 哈希算法: sha1/sha256/sha512"),
) -> Any:
    """计算指定密钥当前的 TOTP 验证码。"""
    return {"result": totp.totp(secret, period=period, digits=digits, algorithm=algorithm)}


@router.post("/2fa/setup", response_model=APIResponse[TotpSetupData])
async def setup(payload: TotpSetupPayload) -> Any:
    """生成 TOTP 密钥及 otpauth:// URI。"""
    secret = totp.generate_secret(payload.length)
    uri = totp.build_uri(
        secret,
        account=payload.account,
        issuer=payload.issuer,
        period=payload.period,
        digits=payload.digits,
        algorithm=payload.algorithm,
    )
    return {"secret": secret, "otpauthUri": uri}


@router.post("/2fa/verify", response_model=APIResponse[TotpVerifyData])
async def verify(payload: TotpVerifyPayload) -> Any:
    """校验 TOTP 验证码, 默认允许前后 1 个时间窗口偏移。"""
    valid = totp.verify(
        payload.secret,
        payload.code,
        window=payload.window,
        period=payload.period,
        digits=payload.digits,
        algorithm=payload.algorithm,
    )
    return {"valid": valid}

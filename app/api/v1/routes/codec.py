"""编解码与 RSA 路由: Base64, Base58, RSA 合并为一个路由组。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.api.dependencies import Container
from app.api.schemas.crypto import RsaDecryptPayload, RsaEncryptPayload, RsaKeyPairData
from app.api.schemas.encoding import DataPayload
from app.api.schemas.response import APIResponse, ResultData
from app.core.algorithms import base64_codec, rsa

router = APIRouter(tags=["codec"])


@router.post("/base64/encode", response_model=APIResponse[ResultData])
async def base64_encode(payload: DataPayload) -> Any:
    """Base64 编码。"""
    return {"result": base64_codec.encode_text(payload.data)}


@router.post("/base64/decode", response_model=APIResponse[ResultData])
async def base64_decode(payload: DataPayload) -> Any:
    """Base64 解码。"""
    return {"result": base64_codec.decode_text(payload.data)}


@router.get("/base58/encode", response_class=PlainTextResponse)
async def base58_encode(
    container: Container,
    url: str = Query(..., description="待编码的 URL，将获取其内容后进行 Base58 编码"),
) -> str:
    """编码远程 URL 内容。"""
    return await container.encoding.encode_url(url)


@router.get("/base58/decode", response_class=PlainTextResponse)
async def base58_decode(
    container: Container,
    url: str = Query(..., description="待解码的 Base58 内容 URL"),
) -> str:
    """解码远程 URL 中的 Base58 内容。"""
    return await container.encoding.decode_url(url)


@router.post("/rsa/generate", response_model=APIResponse[RsaKeyPairData])
async def rsa_generate() -> Any:
    """生成 RSA-OAEP 2048 密钥对。"""
    return rsa.generate_key_pair()


@router.post("/rsa/encrypt", response_model=APIResponse[ResultData])
async def rsa_encrypt(payload: RsaEncryptPayload, container: Container) -> Any:
    """使用公钥加密明文, 未传公钥时使用服务端默认密钥。"""
    public_key = payload.public_key or container.settings.rsa_public_key
    return {"result": rsa.encrypt(payload.data, public_key)}


@router.post("/rsa/decrypt", response_model=APIResponse[ResultData])
async def rsa_decrypt(payload: RsaDecryptPayload, container: Container) -> Any:
    """使用私钥解密密文, 未传私钥时使用服务端默认密钥。"""
    private_key = payload.private_key or container.settings.rsa_private_key
    return {"result": rsa.decrypt(payload.data, private_key)}

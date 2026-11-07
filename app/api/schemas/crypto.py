"""RSA 接口的请求与响应结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RsaEncryptPayload(BaseModel):
    """RSA 加密请求体。"""

    data: str = Field(description="待加密明文")
    public_key: str | None = Field(default=None, alias="publicKey", description="Base64 SPKI 公钥")

    model_config = {"populate_by_name": True}


class RsaDecryptPayload(BaseModel):
    """RSA 解密请求体。"""

    data: str = Field(description="Base64 密文")
    private_key: str | None = Field(
        default=None, alias="privateKey", description="Base64 PKCS8 私钥"
    )

    model_config = {"populate_by_name": True}


class RsaKeyPairData(BaseModel):
    """RSA 密钥对响应数据。"""

    publicKey: str = Field(description="Base64 SPKI 公钥")
    privateKey: str = Field(description="Base64 PKCS8 私钥")

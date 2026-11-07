"""TOTP 接口的请求与响应结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TotpSetupPayload(BaseModel):
    """2FA 密钥生成请求体。"""

    account: str = Field(description="账户标识, 如用户名或邮箱")
    issuer: str = Field(default="API", description="发行方名称")
    length: int = Field(default=20, ge=10, le=64, description="密钥随机字节数")
    period: int = Field(default=30, ge=1, le=300, description="时间步长 (秒)")
    digits: int = Field(default=6, ge=6, le=8, description="验证码位数")
    algorithm: str = Field(default="sha1", description="HMAC 哈希算法: sha1/sha256/sha512")


class TotpVerifyPayload(BaseModel):
    """2FA 验证码校验请求体。"""

    secret: str = Field(description="Base32 编码密钥")
    code: str = Field(description="待校验的 TOTP 验证码")
    window: int = Field(default=1, ge=0, le=5, description="允许的时钟偏移窗口数")
    period: int = Field(default=30, ge=1, le=300, description="时间步长 (秒)")
    digits: int = Field(default=6, ge=6, le=8, description="验证码位数")
    algorithm: str = Field(default="sha1", description="HMAC 哈希算法: sha1/sha256/sha512")


class TotpSetupData(BaseModel):
    """2FA 密钥生成响应数据。"""

    secret: str = Field(description="Base32 编码密钥")
    otpauthUri: str = Field(description="otpauth:// URI, 供验证器 App 扫码导入")


class TotpVerifyData(BaseModel):
    """2FA 验证码校验响应数据。"""

    valid: bool = Field(description="校验是否通过")

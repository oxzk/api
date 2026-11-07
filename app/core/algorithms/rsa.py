"""RSA-OAEP (SHA-256) 加解密, 密钥以 Base64 传输。"""

from __future__ import annotations

import base64
import binascii

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from app.core.exceptions import BadRequestError

RSA_MODULUS_LENGTH = 2048
"""密钥模长。"""

RSA_PUBLIC_EXPONENT = 65537
"""公钥指数。"""

OAEP_PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)
"""统一 OAEP 填充参数。"""


def generate_key_pair() -> dict[str, str]:
    """生成 RSA-OAEP 2048 密钥对。

    Returns:
        Base64 SPKI 公钥与 Base64 PKCS8 私钥
    """
    private_key = rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT,
        key_size=RSA_MODULUS_LENGTH,
    )
    public_key = private_key.public_key()

    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return {
        "publicKey": base64.b64encode(public_der).decode("ascii"),
        "privateKey": base64.b64encode(private_der).decode("ascii"),
    }


def encrypt(data: str, public_key: str) -> str:
    """使用公钥加密明文。

    Args:
        data: 待加密字符串
        public_key: Base64 SPKI 公钥

    Returns:
        Base64 密文

    Raises:
        BadRequestError: 明文或公钥缺失/非法
    """
    if not data:
        raise BadRequestError("data required")
    if not public_key:
        raise BadRequestError("publicKey required")

    encrypted = _import_public_key(public_key).encrypt(data.encode("utf-8"), OAEP_PADDING)
    return base64.b64encode(encrypted).decode("ascii")


def decrypt(data: str, private_key: str) -> str:
    """使用私钥解密密文。

    Args:
        data: Base64 密文
        private_key: Base64 PKCS8 私钥

    Returns:
        解密后的明文

    Raises:
        BadRequestError: 密文或私钥缺失/非法
    """
    if not data:
        raise BadRequestError("data required")
    if not private_key:
        raise BadRequestError("privateKey required")

    try:
        ciphertext = base64.b64decode(data)
    except (binascii.Error, ValueError) as exc:
        raise BadRequestError("invalid ciphertext") from exc

    try:
        decrypted = _import_private_key(private_key).decrypt(ciphertext, OAEP_PADDING)
    except ValueError as exc:
        raise BadRequestError("decrypt failed") from exc
    return decrypted.decode("utf-8")


def _import_public_key(key_b64: str) -> RSAPublicKey:
    """导入 Base64 SPKI 公钥。"""
    try:
        key = serialization.load_der_public_key(base64.b64decode(key_b64))
    except Exception as exc:
        raise BadRequestError("invalid publicKey") from exc
    if not isinstance(key, RSAPublicKey):
        raise BadRequestError("invalid publicKey")
    return key


def _import_private_key(key_b64: str) -> RSAPrivateKey:
    """导入 Base64 PKCS8 私钥。"""
    try:
        key = serialization.load_der_private_key(base64.b64decode(key_b64), password=None)
    except Exception as exc:
        raise BadRequestError("invalid privateKey") from exc
    if not isinstance(key, RSAPrivateKey):
        raise BadRequestError("invalid privateKey")
    return key

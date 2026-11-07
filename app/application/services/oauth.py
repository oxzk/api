"""OAuth redirect_uri 中转用例。

state 内携带 redirect (真实地址)、可选 nonce (业务原始 state) 与任意业务参数。
"""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

from app.core.exceptions import BadRequestError

ALLOWED_PROTOCOLS = {"http", "https"}
"""允许的跳转协议。"""

RESERVED_STATE_KEYS = {"redirect", "nonce"}
"""state 中由中转服务消费的保留键。"""


class OAuthService:
    """解析 state 并构造真实回调地址。"""

    def parse_state(self, raw: str) -> dict[str, str]:
        """解析 OAuth state。

        兼容 base64url JSON、URI 编码 JSON、裸 JSON。

        Args:
            raw: 提供商回传的 state 原文

        Returns:
            中转载荷

        Raises:
            BadRequestError: state 缺失或无法解析出 redirect
        """
        if not raw:
            raise BadRequestError("state required")

        candidates = [raw]
        decoded_uri = self._try_decode_uri(raw)
        if decoded_uri:
            candidates.append(decoded_uri)
        decoded_b64 = self._try_from_base64url(raw)
        if decoded_b64:
            candidates.append(decoded_b64)

        for text in candidates:
            parsed = self._try_parse_json(text)
            if not parsed:
                continue

            redirect = parsed.get("redirect")
            if not isinstance(redirect, str) or not redirect.strip():
                continue

            relay: dict[str, str] = {"redirect": redirect.strip()}
            nonce = parsed.get("nonce")
            if isinstance(nonce, str) and nonce:
                relay["nonce"] = nonce

            for key, value in parsed.items():
                if key in RESERVED_STATE_KEYS:
                    continue
                if isinstance(value, str) and value != "":
                    relay[key] = value
            return relay

        raise BadRequestError("invalid state")

    def assert_redirect_url(self, redirect: str) -> str:
        """校验 redirect 为 http(s) 绝对地址。

        Args:
            redirect: 业务回调地址

        Returns:
            校验通过的地址

        Raises:
            BadRequestError: 协议或主机不合法
        """
        try:
            url = urlparse(redirect)
        except ValueError as exc:
            raise BadRequestError("invalid redirect url") from exc

        if url.scheme not in ALLOWED_PROTOCOLS or not url.netloc:
            raise BadRequestError("redirect must be http or https")
        return redirect

    def build_target_url(self, relay: dict[str, str], params: dict[str, str]) -> str:
        """构造中转目标 URL。

        1. 转发提供商回调上除 state 外的全部参数
        2. 写入 state 中除 redirect / nonce 外的业务参数
        3. 用 nonce 还原查询参数 state

        Args:
            relay: 解析后的中转载荷
            params: 提供商回调上的全部参数

        Returns:
            目标跳转地址
        """
        redirect = self.assert_redirect_url(relay["redirect"])
        parsed = urlparse(redirect)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))

        for key, value in params.items():
            if key == "state" or value is None:
                continue
            query[key] = value

        for key, value in relay.items():
            if key in RESERVED_STATE_KEYS or not value:
                continue
            query[key] = value

        if relay.get("nonce"):
            query["state"] = relay["nonce"]

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode(query),
                parsed.fragment,
            )
        )

    def normalize_params(self, source: dict[str, Any]) -> dict[str, str]:
        """把查询参数归一为字符串字典。

        Args:
            source: 查询参数对象

        Returns:
            字符串字典
        """
        result: dict[str, str] = {}
        for key, value in source.items():
            if value is None:
                continue
            if isinstance(value, list):
                if value:
                    result[key] = str(value[0])
            else:
                result[key] = str(value)
        return result

    @staticmethod
    def _try_parse_json(text: str) -> dict[str, Any] | None:
        """尝试 JSON 解析, 失败返回 None。"""
        try:
            value = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _try_decode_uri(text: str) -> str | None:
        """尝试 URI 解码, 失败或无变化返回 None。"""
        try:
            decoded = unquote(text)
        except ValueError:
            return None
        return decoded if decoded != text else None

    @staticmethod
    def _try_from_base64url(text: str) -> str | None:
        """尝试 base64url 解码为 UTF-8 字符串。"""
        try:
            padded = text.replace("-", "+").replace("_", "/")
            padded += "=" * (-len(padded) % 4)
            return base64.b64decode(padded).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

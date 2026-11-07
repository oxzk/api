"""应用配置入口。

环境变量名与历史版本保持一致, 不做前缀改造, 避免线上配置失效。
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行时配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    # RSA 默认密钥 (Base64 SPKI / PKCS8 DER)
    rsa_public_key: str = ""
    rsa_private_key: str = ""

    # Telegram Bot
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # TinyPNG (tinify) 图片压缩 API Key, 多个用 | 分隔, 每次请求随机取一个
    tinypng_api_key: str = ""

    # 外部请求超时 (秒)
    http_timeout: float = 30.0
    tinypng_timeout: float = 60.0

    # 单次响应体上限 (字节), 防止上游大文件撑爆内存
    max_download_bytes: int = 20 * 1024 * 1024

    @property
    def tinypng_keys(self) -> list[str]:
        """按 ``|`` 拆分的 TinyPNG API Key 列表。"""
        return [key.strip() for key in self.tinypng_api_key.split("|") if key.strip()]


def load_settings() -> Settings:
    """在 lifespan 或依赖中加载配置, 导入时不读取环境。"""
    return Settings()

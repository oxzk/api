"""Composition Root, 所有共享资源只在此组装。"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.services.encoding import EncodingService
from app.application.services.notification import NotificationService
from app.application.services.oauth import OAuthService
from app.application.services.tinypng import TinypngService
from app.application.services.url import UrlProxyService
from app.core.config import Settings, load_settings
from app.infrastructure.http.client import HttpClient
from app.infrastructure.image.tinypng import TinypngDriver
from app.infrastructure.notification.telegram import TelegramDriver
from app.infrastructure.proxy.forward import HttpForwardDriver


@dataclass
class ApplicationContainer:
    """集中保存配置, 共享资源与全部应用服务。"""

    settings: Settings
    http: HttpClient
    tinypng_driver: TinypngDriver
    telegram: TelegramDriver
    encoding: EncodingService
    tinypng: TinypngService
    urls: UrlProxyService
    oauth: OAuthService
    notifications: NotificationService

    @classmethod
    async def create(cls, settings: Settings | None = None) -> ApplicationContainer:
        """按依赖顺序创建共享资源与服务。

        Args:
            settings: 外部注入的配置, 缺省从环境加载

        Returns:
            组装完成的应用容器
        """
        loaded = settings or load_settings()
        http = HttpClient(timeout=loaded.http_timeout)
        tinypng_driver = TinypngDriver(
            http,
            loaded.tinypng_keys,
            timeout=loaded.tinypng_timeout,
        )
        telegram = TelegramDriver(http, loaded.telegram_bot_token)
        forward = HttpForwardDriver(
            http,
            timeout=loaded.http_timeout,
            max_bytes=loaded.max_download_bytes,
        )
        return cls(
            settings=loaded,
            http=http,
            tinypng_driver=tinypng_driver,
            telegram=telegram,
            encoding=EncodingService(
                http,
                timeout=loaded.http_timeout,
                max_bytes=loaded.max_download_bytes,
            ),
            tinypng=TinypngService(
                http,
                driver=tinypng_driver,
                timeout=loaded.http_timeout,
                max_bytes=loaded.max_download_bytes,
            ),
            urls=UrlProxyService(forward),
            oauth=OAuthService(),
            notifications=NotificationService(telegram, loaded.telegram_chat_id),
        )

    async def shutdown(self) -> None:
        """释放共享资源。"""
        await self.http.close()

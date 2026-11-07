"""日志工具模块。"""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
"""统一日志格式。"""


def build_logger(name: str = "api") -> logging.Logger:
    """构建应用日志实例。

    Args:
        name: logger 名称

    Returns:
        配置完成的 Logger 实例
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


logger = build_logger()
"""全局日志实例。"""

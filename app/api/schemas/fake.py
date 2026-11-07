"""假数据接口的响应结构。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FakeNameData(BaseModel):
    """假数据姓名响应。"""

    firstName: str = Field(description="名")
    lastName: str = Field(description="姓")
    fullName: str = Field(description="全名")
    username: str = Field(description="用户名")
    password: str = Field(description="随机密码, 含大小写字母、数字与符号")

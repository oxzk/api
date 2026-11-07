"""假数据生成路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.schemas.fake import FakeNameData
from app.api.schemas.response import APIResponse
from app.core.fake import Fake

router = APIRouter(prefix="/fake", tags=["fake"])


@router.get("", response_model=APIResponse[FakeNameData])
async def generate_fake() -> Any:
    """生成随机英文姓名、用户名与密码。"""
    first_name = Fake.first_name()
    last_name = Fake.last_name()
    return {
        "firstName": first_name,
        "lastName": last_name,
        "fullName": f"{first_name} {last_name}",
        "username": Fake.username(first_name, last_name),
        "password": Fake.password(),
    }

"""假数据生成工具。"""

from __future__ import annotations

import secrets

FIRST_NAMES = [
    "James",
    "John",
    "Robert",
    "Michael",
    "David",
    "William",
    "Richard",
    "Joseph",
    "Thomas",
    "Christopher",
    "Charles",
    "Daniel",
    "Matthew",
    "Anthony",
    "Mark",
    "Donald",
    "Steven",
    "Paul",
    "Andrew",
    "Joshua",
    "Mary",
    "Patricia",
    "Jennifer",
    "Linda",
    "Barbara",
    "Elizabeth",
    "Susan",
    "Jessica",
    "Sarah",
    "Karen",
    "Lisa",
    "Nancy",
    "Betty",
    "Margaret",
    "Sandra",
    "Ashley",
    "Kimberly",
    "Emily",
    "Donna",
    "Michelle",
    "Emma",
    "Olivia",
    "Ava",
    "Isabella",
    "Sophia",
    "Mia",
    "Charlotte",
    "Amelia",
    "Harper",
    "Evelyn",
    "Liam",
    "Noah",
    "Oliver",
    "Elijah",
    "Lucas",
    "Mason",
    "Logan",
    "Alexander",
    "Ethan",
    "Jacob",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
]

PASSWORD_CHARS = {
    "lower": "abcdefghijklmnopqrstuvwxyz",
    "upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "digits": "0123456789",
    "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
}


def random_int(max_value: int) -> int:
    """使用密码学安全随机源生成 [0, max_value) 整数。

    Args:
        max_value: 上界 (不含)

    Returns:
        随机整数
    """
    if max_value <= 0:
        return 0
    return secrets.randbelow(max_value)


class Fake:
    """假数据生成器。"""

    @staticmethod
    def pick(arr: list[str]) -> str:
        """从列表中随机取一项。"""
        return arr[random_int(len(arr))]

    @staticmethod
    def pick_char(text: str) -> str:
        """从字符串中随机取一个字符。"""
        return text[random_int(len(text))]

    @classmethod
    def first_name(cls) -> str:
        """随机英文名。"""
        return cls.pick(FIRST_NAMES)

    @classmethod
    def last_name(cls) -> str:
        """随机英文姓。"""
        return cls.pick(LAST_NAMES)

    @classmethod
    def full_name(cls) -> str:
        """随机全名。"""
        return f"{cls.first_name()} {cls.last_name()}"

    @classmethod
    def email(cls, domain: str | None = None) -> str:
        """生成随机邮箱。"""
        first = cls.first_name().lower()
        last = cls.last_name().lower()
        suffix = domain or "example.com"
        num = cls.password(3, lower=False, upper=False, digits=True, symbols=False)
        return f"{first}.{last}{num}@{suffix}"

    @classmethod
    def username(cls, first_name: str | None = None, last_name: str | None = None) -> str:
        """生成用户名: first.last + 4 位随机数字。

        Args:
            first_name: 可选名, 未传则随机
            last_name: 可选姓, 未传则随机
        """
        first = (first_name or cls.first_name()).lower()
        last = (last_name or cls.last_name()).lower()
        num = str(random_int(10000)).zfill(4)
        return f"{first}.{last}{num}"

    @classmethod
    def password(
        cls,
        length: int = 16,
        *,
        lower: bool = True,
        upper: bool = True,
        digits: bool = True,
        symbols: bool = True,
    ) -> str:
        """生成随机密码, 保证各启用字符类至少出现一次。

        Args:
            length: 密码长度
            lower: 是否包含小写
            upper: 是否包含大写
            digits: 是否包含数字
            symbols: 是否包含符号
        """
        chars = ""
        required: list[str] = []

        if lower:
            chars += PASSWORD_CHARS["lower"]
            required.append(cls.pick_char(PASSWORD_CHARS["lower"]))
        if upper:
            chars += PASSWORD_CHARS["upper"]
            required.append(cls.pick_char(PASSWORD_CHARS["upper"]))
        if digits:
            chars += PASSWORD_CHARS["digits"]
            required.append(cls.pick_char(PASSWORD_CHARS["digits"]))
        if symbols:
            chars += PASSWORD_CHARS["symbols"]
            required.append(cls.pick_char(PASSWORD_CHARS["symbols"]))

        if not chars:
            chars = PASSWORD_CHARS["lower"]
            required.append(cls.pick_char(PASSWORD_CHARS["lower"]))

        remaining = length - len(required)
        for _ in range(max(0, remaining)):
            required.append(cls.pick_char(chars))

        # Fisher-Yates 洗牌
        for i in range(len(required) - 1, 0, -1):
            j = random_int(i + 1)
            required[i], required[j] = required[j], required[i]

        return "".join(required)

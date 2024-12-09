from pydantic import BaseModel
from typing import Optional


class UserConfig(BaseModel):
    """A Config Item to serialize yaml users"""

    username: str
    password: str
    email: Optional[str] = None
    groups: list[str] = []

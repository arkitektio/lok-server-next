from pydantic import BaseModel
from typing import Optional


class UserConfig(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    groups: list[str] = []

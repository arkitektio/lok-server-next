from pydantic import BaseModel
from typing import Optional


class MembershipConfig(BaseModel):
    organization: str
    is_active: bool = True
    user: str
    roles: list[str] = []


class UserConfig(BaseModel):
    """A Config Item to serialize yaml users"""

    username: str
    password: str
    email: Optional[str] = None
    is_superuser: bool = False
    is_staff: bool = False


class OrganizationConfig(BaseModel):
    name: str
    owner: str
    description: Optional[str] = None
    identifier: Optional[str] = None
    parent: Optional[str] = None
    auto_configure: bool = True


class Members(BaseModel):
    memberships: list[MembershipConfig] = []

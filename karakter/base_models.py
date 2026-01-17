from pydantic import BaseModel
from typing import Optional


class MembershipConfig(BaseModel):
    organization: str
    is_active: bool = True
    roles: list[str] = []


class UserConfig(BaseModel):
    """A Config Item to serialize yaml users"""

    username: str
    password: str
    email: Optional[str] = None
    memberships: list[MembershipConfig] = []


class OrganizationConfig(BaseModel):
    name: str
    owner: str
    description: Optional[str] = None
    identifier: Optional[str] = None
    parent: Optional[str] = None


class Members(BaseModel):
    memberships: list[MembershipConfig] = []

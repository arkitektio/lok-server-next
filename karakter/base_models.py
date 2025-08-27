from pydantic import BaseModel
from typing import Optional




class OrganizationConfig(BaseModel):
    name: str
    description: Optional[str] = None
    identifier: Optional[str] = None
    parent: Optional[str] = None
    
    
class RoleConfig(BaseModel):
    organization: str
    identifier: str
    description: Optional[str] = None
    


class MembershipConfig(BaseModel):
    organization: str
    is_active: bool = True
    roles: list[str] = []



class UserConfig(BaseModel):
    """A Config Item to serialize yaml users"""

    username: str
    password: str
    active_organization: str
    email: Optional[str] = None
    memberships: list[MembershipConfig] = []

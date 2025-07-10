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
    


class UserConfig(BaseModel):
    """A Config Item to serialize yaml users"""

    username: str
    password: str
    email: Optional[str] = None
    roles: list[str] = []
    active_organization: Optional[str] = None

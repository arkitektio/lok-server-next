from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TailnetCreate(BaseModel):
    name: str = Field(..., description="The unique name of the tailnet")
    # Add other create-time options here if needed (e.g., OIDC settings)


class Tailnet(BaseModel):
    id: str
    name: str
    dns_name: Optional[str] = None
    created_at: Optional[datetime] = None

    # Use ConfigDict for Pydantic v2, or class Config for v1
    model_config = {"from_attributes": True}


class TailnetList(BaseModel):
    tailnets: List[Tailnet]


class Machine(BaseModel):
    id: str
    name: str
    tailnet: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    ephemeral: bool = False
    connected: bool = False
    last_seen: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}

class MachineDetail(Machine):
    os: Optional[str] = None
    key_expiry: Optional[datetime] = None
    authorized: bool = False
    is_external: bool = False
    
    # Add other fields as needed based on `ionscale machines get` output


class MachineList(BaseModel):
    machines: List[Machine]

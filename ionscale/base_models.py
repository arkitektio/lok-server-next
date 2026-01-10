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

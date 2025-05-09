from kante.channel import build_channel
from pydantic import BaseModel

class Communication(BaseModel):
    id: str


communication_channel = build_channel(Communication)

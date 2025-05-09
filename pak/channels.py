from kante.channel import build_channel
from pydantic import BaseModel

class StashSignal(BaseModel):
    id: str


stash_channel = build_channel(StashSignal)

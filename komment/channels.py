from kante.channel import build_channel
from pydantic import BaseModel

class MentionSignal(BaseModel):
    id: str

mention_channel = build_channel(MentionSignal)

from strawberry.types import Info as _Info
from ekke.context import ChannelsWSContext
from typing import Any

Info = _Info[ChannelsWSContext, Any]

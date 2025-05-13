from kante.types import Info
import strawberry_django
import strawberry
from karakter import types, models, scalars
from typing import AsyncGenerator
from karakter.channels import communication_channel


async def communications(
    self, info: Info, channels: list[strawberry.ID]
) -> AsyncGenerator[types.Communication, None]:
    """Join and subscribe to message sent to the given rooms."""
    async for message in communication_channel(info, channels):
        yield await models.AssignationEvent.objects.aget(id=message)

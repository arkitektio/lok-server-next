from ekke.types import Info
import strawberry_django
import strawberry
from karakter import types, models, scalars
from typing import AsyncGenerator
from karakter.channels import communicatoin_listen


async def communications(
    self, info: Info, channels: list[strawberry.ID]
) -> AsyncGenerator[types.Communication, None]:
    """Join and subscribe to message sent to the given rooms."""
    async for message in communicatoin_listen(info, channels):
        yield await models.AssignationEvent.objects.aget(id=message)

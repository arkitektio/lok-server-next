from ekke.types import Info
import strawberry_django
import strawberry
from komment import types, models, scalars
from typing import AsyncGenerator
from komment.channels import mention_listen


async def mentions(self, info: Info) -> AsyncGenerator[types.Comment, None]:
    """Join and subscribe to message sent to the given rooms."""
    async for message in mention_listen(
        info, ["user-" + str(info.context.request.user.id)]
    ):
        yield await models.Comment.objects.aget(id=message)

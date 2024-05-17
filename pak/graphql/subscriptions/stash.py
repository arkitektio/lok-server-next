from ekke.types import Info
import strawberry_django
import strawberry
from pak import types, models, scalars
from typing import AsyncGenerator
from pak.channels import stash_changed_listen


@strawberry.type(description="Subscription to stash items.")
class StashEvent:
    create: types.StashItem | None
    update: types.StashItem | None
    delete: str



async def stash_items(
    self, info: Info, stash: strawberry.ID
) -> AsyncGenerator[StashEvent, None]:
    """Join and subscribe to message sent to the given rooms."""
    async for message in stash_changed_listen(info, [f"stash_{stash}"]):
        print("ID", message)
        yield message


from ekke.types import Info
import strawberry_django
import strawberry
from pak import types, models, inputs, enums, scalars
import logging

logger = logging.getLogger(__name__)


def stash(info: Info, id: strawberry.ID) -> types.Stash:

    user = info.context.request.user

    stash = models.Stash.objects.get(id=id, user=user)

    return stash

def my_stashes(info: Info) -> list[types.Stash]:

    user = info.context.request.user

    stashes = models.Stash.objects.filter(user=user)

    return stashes

def stash_item(info: Info, id: strawberry.ID) -> types.StashItem:

    user = info.context.request.user

    stash = models.Stash.objects.get(id=id, user=user)

    items = models.StashItem.objects.filter(stash=stash)

    return items
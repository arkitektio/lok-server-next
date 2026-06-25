
import strawberry
from kante.types import Info
from karakter import models, types


def user(info: Info, id: strawberry.ID) -> types.User:
    return models.User.objects.get(id=id)


def me(info: Info) -> types.User:
    return info.context.request.user





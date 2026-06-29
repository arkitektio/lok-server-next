
import strawberry
from kante.types import Info
from karakter import models, types


def group(info: Info, id: strawberry.ID) -> types.Group:
    return models.Group.objects.get(id=id)


def mygroups(info: Info) -> list[types.Group]:
    return info.context.request.user.groups.all()

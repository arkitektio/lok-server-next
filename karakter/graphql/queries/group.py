import hashlib
import json
import logging

import strawberry
from ekke.types import Info
from karakter import enums, inputs, models, scalars, types


def group(info: Info, id: strawberry.ID) -> types.Group:
    return models.Group.objects.get(id=id)


def mygroups(info: Info) -> list[types.Group]:
    return info.context.request.user.groups.all()
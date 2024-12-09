import hashlib
import json
import logging

import strawberry
from ekke.types import Info
from karakter import enums, inputs, models, scalars, types


def user(info: Info, id: strawberry.ID) -> types.User:
    return models.User.objects.get(id=id)


def me(info: Info) -> types.User:
    return info.context.request.user

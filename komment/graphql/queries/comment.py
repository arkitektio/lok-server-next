import hashlib
import json
import logging

import strawberry
from kante.types import Info
from komment import enums, inputs, models, scalars, types


def comment(info: Info, id: strawberry.ID) -> types.Comment:
    return models.Comment.objects.get(id=id)


def comments_for(
    info: Info, identifier: scalars.Identifier, object: strawberry.ID
) -> list[types.Comment]:
    return models.Comment.objects.filter(identifier=identifier, object=object)


def my_mentions(info: Info) -> list[types.Comment]:
    return models.Comment.objects.filter(mentions=info.context.request.user)

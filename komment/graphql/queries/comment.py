import hashlib
import json
import logging

import strawberry
from ekke.types import Info
from komment import enums, inputs, models, scalars, types


def comment(info: Info, id: strawberry.ID) -> types.Comment:
    return models.Comment.objects.get(id=id)

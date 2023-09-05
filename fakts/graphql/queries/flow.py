import hashlib
import json
import logging

import strawberry
import strawberry_django
from facade.protocol import infer_protocols
from facade.utils import hash_input
from ekke.types import Info
from karakter import enums, inputs, models, scalars, types


def flow(info: Info, id: strawberry.ID) -> types.Flow:
    return models.Flow.objects.get(id=id)
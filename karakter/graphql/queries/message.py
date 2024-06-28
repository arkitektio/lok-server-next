import hashlib
import json
import logging

import strawberry
from ekke.types import Info
from karakter import enums, inputs, models, scalars, types


def message(info: Info, id: strawberry.ID) -> types.SystemMessage:
    return models.SystemMessage.objects.get(id=id)


def my_active_messages(info: Info) -> list[types.SystemMessage]:

    messages = models.SystemMessage.objects.filter(
        user=info.context.request.user, acknowledged=False
    )
    return messages.all()

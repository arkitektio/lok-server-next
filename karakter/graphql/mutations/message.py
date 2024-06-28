import hashlib
import json
import logging

import namegenerator
import strawberry
import strawberry_django
from ekke.types import Info
from karakter import enums, inputs, models, scalars, types
from karakter.hashers import hash_graph

logger = logging.getLogger(__name__)


@strawberry.input
class AcknowledgeMessageInput:
    id: strawberry.ID
    acknowledged: bool


def acknowledge_message(
    info: Info, input: AcknowledgeMessageInput
) -> types.SystemMessage:
    message = models.SystemMessage.objects.get(id=input.id)
    message.acknowledged = input.acknowledged
    message.save()
    return message

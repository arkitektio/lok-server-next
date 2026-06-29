import logging

import strawberry
from kante.types import Info
from karakter import models, types

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

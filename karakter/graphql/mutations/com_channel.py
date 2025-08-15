import hashlib
import json
import logging
import namegenerator
import strawberry
import strawberry_django
from kante.types import Info
from karakter import enums, inputs, models, scalars, types
from karakter.hashers import hash_graph

logger = logging.getLogger(__name__)


@strawberry.input
class RegisterComChannelInput:
    token: str


def register_com_channel(info: Info, input: RegisterComChannelInput) -> types.ComChannel:
    channel, _ = models.ComChannel.objects.update_or_create(
        user=info.context.request.user,
        defaults={"token": input.token},
    )
    return channel


@strawberry.input
class NotifyUserInput:
    user: strawberry.ID
    message: str
    title: str


def notify_user(info: Info, input: NotifyUserInput) -> bool:
    user = models.User.objects.get(id=input.user)

    # Send notification to user
    user.notify(input.message, input.title)
    return True

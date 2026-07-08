import logging
import uuid

import strawberry
from kante.types import Info

from fakts import models, types

logger = logging.getLogger(__name__)


@strawberry.input
class RedeemTokenInput:
    token: str | None = None


def create_redeem_token(info: Info, input: RedeemTokenInput) -> types.RedeemToken:
    uuid_token = uuid.uuid4().hex

    user = info.context.request.user
    hub = info.context.request.client.hub

    token, _ = models.RedeemToken.objects.update_or_create(
        token=uuid_token,
        defaults={
            "user": user,
            "hub": hub,
        },
    )

    print(f"Token {token} created for user {user} and hub {hub}")

    return token

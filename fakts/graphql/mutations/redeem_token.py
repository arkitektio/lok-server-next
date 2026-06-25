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
    composition = info.context.request.client.composition

    token, _ = models.RedeemToken.objects.update_or_create(
        token=uuid_token,
        defaults={
            "user": user,
            "composition": composition,
        },
    )

    print(f"Token {token} created for user {user} and composition {composition}")

    return token

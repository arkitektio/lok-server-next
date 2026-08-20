import logging
import uuid
from datetime import timedelta

import strawberry
from django.utils import timezone
from graphql import GraphQLError
from kante.types import Info

from fakts import models, types
from karakter.authz import DENIED, get_user

logger = logging.getLogger(__name__)

# A redeem token is a bearer credential for creating a client; it must not be
# valid forever. Matches the invite default.
REDEEM_TOKEN_TTL = timedelta(days=7)


@strawberry.input
class RedeemTokenInput:
    token: str | None = None


def create_redeem_token(info: Info, input: RedeemTokenInput) -> types.RedeemToken:
    uuid_token = uuid.uuid4().hex

    user = get_user(info)
    client = getattr(info.context.request, "client", None)
    hub = getattr(client, "hub", None)
    if hub is None:
        # Tokens are issued *for a hub*; a caller whose client composes against
        # no hub has nothing to issue a token for.
        raise GraphQLError(DENIED)

    token, _ = models.RedeemToken.objects.update_or_create(
        token=uuid_token,
        defaults={
            "user": user,
            "hub": hub,
            "expires_at": timezone.now() + REDEEM_TOKEN_TTL,
        },
    )

    logger.info("Redeem token %s created for user %s and hub %s", token.id, user.id, hub.id)

    return token

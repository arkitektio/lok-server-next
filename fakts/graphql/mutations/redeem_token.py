import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from kante.types import Info
import kante

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest, Requirement
from fakts.builders import create_client

logger = logging.getLogger(__name__)


@strawberry.input
class RedeemTokenInput:
    token: str | None = None


def create_redeem_token(info: Info, input: RedeemTokenInput) -> types.RedeemToken:
    uuid_token = uuid.uuid4().hex


    user = info.context.request.user
    org = info.context.request.organization

    token, _ = models.RedeemToken.objects.update_or_create(
        token=input.token or token,
        defaults={
            "user": user,
            "organization": org,
        },
    )

    print(f"Token {token} created for user {user} and organization {org.slug}")

    return token

from datetime import timedelta

import strawberry
from django.utils import timezone
from kante import Info

import api.management.types as types
import kante
from fakts import models as fakts_models


@kante.input
class CreateRedeemTokenInput:
    composition: strawberry.ID
    expires_in_days: int | None = None


def create_redeem_token(info: Info, input: CreateRedeemTokenInput) -> types.ManagementRedeemToken:
    composition = fakts_models.Composition.objects.get(id=input.composition)

    if not composition.organization.memberships.filter(user=info.context.request.user).exists():
        raise Exception("You are not allowed to create redeem tokens for this composition")

    expires_at = None
    if input.expires_in_days:
        expires_at = timezone.now() + timedelta(days=input.expires_in_days)

    return fakts_models.RedeemToken.objects.create(
        user=info.context.request.user,
        organization=composition.organization,
        composition=composition,
        expires_at=expires_at,
    )
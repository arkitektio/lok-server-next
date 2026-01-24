from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from fakts import models
from karakter.models import Organization
from fakts.config_models import RedeemTokenConfigs

# assign directory
directory = "files"

# iterate over files in
# that directory


class Command(BaseCommand):
    help = "Creates redeem tokens for users defined in settings.REDEEM_TOKENS"

    def handle(self, *args, **kwargs):
        TOKENS = settings.REDEEM_TOKENS

        tokens = RedeemTokenConfigs(tokens=TOKENS)

        for token in tokens.tokens:
            user = get_user_model().objects.get(username=token.user)
            composition = models.Composition.objects.get(organization__slug=token.organization, identifier=token.composition)

            token, _ = models.RedeemToken.objects.update_or_create(
                token=token.token,
                defaults={
                    "user": user,
                    "composition": composition,
                },
            )

            print(f"Token {token.token} created for user {user} and composition {composition}")

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from fakts import models
from karakter.models import Organization


# assign directory
directory = "files"

# iterate over files in
# that directory


class Command(BaseCommand):
    help = "Creates redeem tokens for users defined in settings.REDEEM_TOKENS"

    def handle(self, *args, **kwargs):
        TOKENS = settings.REDEEM_TOKENS

        for token in TOKENS:
            user = get_user_model().objects.get(username=token["user"])
            org = Organization.objects.get(slug=token["organization"])

            token, _ = models.RedeemToken.objects.update_or_create(
                token=token["token"],
                defaults={
                    "user": user,
                    "organization": org,
                },
            )

            print(f"Token {token} created for user {user} and organization {org.slug}")

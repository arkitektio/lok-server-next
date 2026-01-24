import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from fakts import models, builders, base_models
import json
import omegaconf
from pydantic import BaseModel


class OpenIDAppConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uris: list[str]


class Command(BaseCommand):
    help = "Creates all configured apps or overwrites them"

    def handle(self, *args, **options):
        apps = settings.ENSURED_OPENID_APPS or []

        for app in apps:
            config = OpenIDAppConfig(**app)

            try:
                client = models.OAuth2Client.objects.get(client_id=config.client_id)
                client.client_secret = config.client_secret
                client.redirect_uris = " ".join(config.redirect_uris)
                client.scope = "openid profile email"
                client.save()

                self.stdout.write(f"Updated OpenID client {client.client_id}")

            except models.OAuth2Client.DoesNotExist:
                client = models.OAuth2Client.objects.create(
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    redirect_uris=" ".join(config.redirect_uris),
                    scope="openid profile email",
                )

                self.stdout.write(f"Created OpenID client {client.client_id}")

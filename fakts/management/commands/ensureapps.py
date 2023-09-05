import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from fakts import models, builders, base_models
import json
import omegaconf


class Command(BaseCommand):
    help = "Creates all configured apps or overwrites them"

    def handle(self, *args, **options):
        apps = settings.ENSURED_APPS or []

        for app in apps:
            config = base_models.AppConfig(**app)

            for client in config.clients:
                client  = builders.create_client(
                    config,
                    client,
                )
                self.stdout.write(f"Created client {client.client_id} for app {config.identifier}")

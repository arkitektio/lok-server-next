from email.headerregistry import Group
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from fakts.models import Layer


class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        layers = settings.FAKTS_LAYERS

        # TODO: Implement validaiton of superusers

        for layer in layers:
            layer, c = Layer.objects.update_or_create(
                identifier=str(layer["IDENTIFIER"]),
                defaults=dict(name=str(layer["NAME"]),
                description=str(layer["DESCRIPTION"]),
                kind=str(layer["KIND"]),
                dns_probe=layer.get("DNS_PROBE", None),
                get_probe=layer.get("GET_PROBE", None),
                logo=layer.get("LOGO", None))
            )
            if c:
                print(f"Created layer {layer}")


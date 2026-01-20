import yaml
from django.core.management.base import BaseCommand
from fakts.models import Layer, Service, ServiceInstance, InstanceAlias, ServiceRelease, Composition, KommunityPartner
from karakter.models import Organization, Role, Scope
from authapp.models import OAuth2Client
from fakts.config_models import KommunityPartnerConfigModel  # <-- Your validated Pydantic schema
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


User = get_user_model()


class Command(BaseCommand):
    help = "Import layers, service instances and compositions from YAML"

    def handle(self, *args, **options):
        partners_config = settings.KOMMUNITY_PARTNERS

        # Validate YAML structure
        config = KommunityPartnerConfigModel(partners=partners_config)


        for partner in config.partners:
            
            x, _ = KommunityPartner.objects.get_or_create(
                identifier=partner.identifier,
                defaults={
                    "name": partner.name,
                    "website_url": partner.website_url,
                    "description": partner.description,
                    "logo_url": partner.logo_url,
                    "auth_url": partner.auth_url,
                },
            )

            try:
                client = OAuth2Client.objects.get(client_id=partner.oauth2.client_id)
                client.client_secret = partner.oauth2.client_secret
                client.redirect_uris = " ".join(partner.oauth2.redirect_uris)
                client.scope = "openid profile email"
                client.save()

                self.stdout.write(f"Updated OpenID client {client.client_id}")

            except OAuth2Client.DoesNotExist:
                client = OAuth2Client.objects.create(
                    client_id=partner.oauth2.client_id,
                    client_secret=partner.oauth2.client_secret,
                    redirect_uris=" ".join(partner.oauth2.redirect_uris),
                    scope="openid profile email",
                )

                self.stdout.write(f"Created OpenID client {client.client_id}")

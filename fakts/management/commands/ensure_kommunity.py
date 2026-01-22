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
    help = "Import kommunity partners from YAML configuration. This command should be run before users and organizations are created."

    def handle(self, *args, **options):
        partners_config = settings.KOMMUNITY_PARTNERS

        # Validate YAML structure
        config = KommunityPartnerConfigModel(partners=partners_config)

        for partner in config.partners:
            # Prepare preconfigured composition data if present
            preconfigured_composition_data = None
            if partner.preconfigured_composition:
                preconfigured_composition_data = partner.preconfigured_composition.model_dump()

            # First, handle the OAuth2 client if present
            oauth_client = None
            if partner.oauth2:
                try:
                    oauth_client = OAuth2Client.objects.get(client_id=partner.oauth2.client_id)
                    oauth_client.client_secret = partner.oauth2.client_secret
                    oauth_client.redirect_uris = " ".join(partner.oauth2.redirect_uris)
                    oauth_client.scope = "openid profile email"
                    oauth_client.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated OpenID client {oauth_client.client_id}"))
                except OAuth2Client.DoesNotExist:
                    oauth_client = OAuth2Client.objects.create(
                        client_id=partner.oauth2.client_id,
                        client_secret=partner.oauth2.client_secret,
                        redirect_uris=" ".join(partner.oauth2.redirect_uris),
                        scope="openid profile email",
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created OpenID client {oauth_client.client_id}"))

            # Create or update the KommunityPartner
            kommunity_partner, created = KommunityPartner.objects.update_or_create(
                identifier=partner.identifier,
                defaults={
                    "name": partner.name,
                    "website_url": partner.website_url,
                    "description": partner.description,
                    "logo_url": partner.logo_url,
                    "auth_url": partner.auth_url,
                    "partner_kind": partner.partner_kind.value,
                    "kommunity_kind": partner.kommunity_kind.value,
                    "auto_configure": partner.auto_configure,
                    "preconfigured_composition": preconfigured_composition_data,
                    "oauth_client": oauth_client,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created KommunityPartner: {kommunity_partner.identifier}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated KommunityPartner: {kommunity_partner.identifier}"))

            if partner.preconfigured_composition:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  -> Preconfigured composition: {partner.preconfigured_composition.identifier}"
                    )
                )
            if partner.auto_configure:
                self.stdout.write(
                    self.style.WARNING(
                        f"  -> Auto-configure enabled: compositions will be created for new organizations"
                    )
                )

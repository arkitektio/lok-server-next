from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import OrganizationConfig
from karakter.models import Organization
from fakts.models import KommunityPartner
from fakts.logic import create_composition_from_partner

User = get_user_model()


class Command(BaseCommand):
    help = "Creates all default organisations if it doesn't exist and applies auto-configured kommunity partners"

    def handle(self, *args, **kwargs):
        organizations = settings.ENSURE_ORGANIZATIONS

        for lokuser in organizations:
            org_config = OrganizationConfig(**lokuser)

            owner = None
            if org_config.owner:
                owner = User.objects.filter(username=org_config.owner).first()
                if not owner:
                    self.stdout.write(self.style.WARNING(f"Owner {org_config.owner} not found for org {org_config.identifier}"))

            if not owner:
                # Fallback to superuser
                owner = User.objects.filter(is_superuser=True).first()

            org_created = False
            if Organization.objects.filter(slug=org_config.identifier).exists():
                org = Organization.objects.get(slug=org_config.identifier)
                org.description = org_config.description
                org.name = org_config.name
                if owner:
                    org.owner = owner
                org.save()

                self.stdout.write(self.style.SUCCESS(f"Updated org {org.slug}"))
            else:
                org = Organization.objects.create(
                    slug=org_config.identifier,
                    name=org_config.name,
                    description=org_config.description,
                    owner=owner
                )
                org_created = True
                self.stdout.write(self.style.SUCCESS(f"Created org {org.slug}"))

            # Apply auto-configure kommunity partners for new organizations
            if org_created:
                auto_configure_partners = KommunityPartner.objects.filter(auto_configure=True)
                for partner in auto_configure_partners:
                    if partner.preconfigured_composition:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Applying auto-configure partner '{partner.identifier}' to org '{org.slug}'"
                            )
                        )
                        
                        # Create a logging function that uses management command styling
                        def log_message(msg: str):
                            self.stdout.write(self.style.SUCCESS(f"  {msg}"))
                        
                        create_composition_from_partner(
                            partner=partner,
                            organization=org,
                            creator=owner,
                            log=log_message,
                        )

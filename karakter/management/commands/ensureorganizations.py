from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import OrganizationConfig
from karakter.models import Organization

User = get_user_model()


class Command(BaseCommand):
    help = "Creates all default organisations if it doesn't exist"

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
                #
                owner = User.objects.filter(is_superuser=True).first()

            if Organization.objects.filter(slug=org_config.identifier).exists():
                org = Organization.objects.get(slug=org_config.identifier)
                org.description = org_config.description
                org.name = org_config.name
                if owner:
                    org.owner = owner
                org.save()

                self.stdout.write(self.style.SUCCESS(f"Updated org {org.slug}"))
            else:
                org = Organization.objects.create(slug=org_config.identifier, name=org_config.name, description=org_config.description, owner=owner)

                self.stdout.write(self.style.SUCCESS(f"Created org {org.slug}"))

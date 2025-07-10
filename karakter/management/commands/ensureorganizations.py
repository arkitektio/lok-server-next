from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig, OrganizationConfig
from karakter.models import Organization, Role





def create_default_groups_for_org(org):
    for identifier in ["admin", "guest", "researcher"]:
        g, _  = Group.objects.get_or_create(name=f"{org.identifier}:{identifier}")
        Role.objects.update_or_create(group=g, identifier=identifier, organization=org)



class Command(BaseCommand):
    help = "Creates all default organisations if it doesn't exist"

    def handle(self, *args, **kwargs):
        organizations = settings.ENSURE_ORGANIZATIONS

        for lokuser in organizations:
            org_config = OrganizationConfig(**lokuser)

            if Organization.objects.filter(identifier=org_config.identifier).exists():
                org = Organization.objects.get(identifier=org_config.identifier)
                org.description = org_config.description
                org.name = org_config.name
                org.save()

                self.stdout.write(f"Updated org {org.identifier}")
            else:
                org = Organization.objects.create(
                    identifier=org_config.identifier,
                    name=org_config.name,
                    description=org_config.description,
                )

                self.stdout.write(f"Created org {org.identifier}")
                 
            create_default_groups_for_org(org)

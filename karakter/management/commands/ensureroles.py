from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import RoleConfig
from karakter.models import Organization, Role
from karakter.managers import create_role




class Command(BaseCommand):
    help = "Creates all lok user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        lokroles = settings.ENSURED_ROLES

        for role_dict in lokroles:
            role_config = RoleConfig(**role_dict)
            
            org = Organization.objects.get(identifier=role_config.organization)
            group_name = f"{org.identifier}:{role_config.identifier}"
            group, _ = Group.objects.get_or_create(name=group_name)
            role, created = Role.objects.update_or_create(
                organization=org,
                identifier=role_config.identifier,
                defaults={"group": group, "description": role_config.description}
            )
            
            if created:
                self.stdout.write(f"Created role {role.identifier} for organization {org.identifier}")
            else:
                self.stdout.write(f"Updated role {role.identifier} for organization {org.identifier}")
            
                
                
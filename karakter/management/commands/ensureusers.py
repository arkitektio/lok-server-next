from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig
from karakter.models import Organization





class Command(BaseCommand):
    help = "Creates all lok user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        lokusers = settings.ENSURED_USERS

        for lokuser in lokusers:
            user_config = UserConfig(**lokuser)

            User = get_user_model()
            if User.objects.filter(username=user_config.username).exists():
                user = User.objects.get(username=user_config.username)
                user.email = user_config.email
                user.active_organization = Organization.objects.get(
                    identifier=user_config.active_organization
                )
                user.set_password(user_config.password.strip())
                user.save()

                self.stdout.write(f"Updated user {user.username}")
            else:
                user = User.objects.create_user(
                    username=user_config.username,
                    email=user_config.email,
                    password=user_config.password,
                    active_organization = Organization.objects.get(
                    identifier=user_config.active_organization
                )
                )

                self.stdout.write(f"Created user {user.username}")
                
                
                
            user.groups.add(
                *[
                    Group.objects.get(name=groupname)
                    for groupname in user_config.roles
                ]
            )
            
            print(f"Added groups {user_config.roles} to user {user.username}")

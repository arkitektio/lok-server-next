from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig


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
                user.set_password(user_config.password.strip())
                user.save()

                self.stdout.write(f"Updated user {user.username}")
            else:
                user = User.objects.create_user(
                    username=user_config.username,
                    email=user_config.email,
                    password=user_config.password,
                )

                self.stdout.write(f"Created user {user.username}")
            user.groups.add(
                *[
                    Group.objects.get_or_create(name=groupname)[0]
                    for groupname in user_config.groups
                ]
            )

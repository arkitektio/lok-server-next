from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig
from karakter.models import Organization, User, Role, Membership


class Command(BaseCommand):
    help = "Creates all lok user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        lokusers = settings.ENSURED_USERS

        for lokuser in lokusers:
            try:
                user_config = UserConfig(**lokuser)

                if User.objects.filter(username=user_config.username).exists():
                    user = User.objects.get(username=user_config.username)
                    user.email = user_config.email
                    user.set_password(user_config.password.strip())
                    user.save()

                    self.stdout.write(f"Updated user {user.username}")
                else:
                    user = User.objects.create_user(username=user_config.username, email=user_config.email, password=user_config.password)
                    self.stdout.write(f"Created user {user.username}")

                # Clear existing memberships
                Membership.objects.filter(user=user).delete()

                # Add user to groups based on roles
                for membershipc in user_config.memberships:
                    org = Organization.objects.get(slug=membershipc.organization)

                    membership, _ = Membership.objects.update_or_create(
                        user=user,
                        organization=org,
                    )

                    for role in membershipc.roles:
                        role = Role.objects.get(organization=org, identifier=role)

                        membership.roles.add(role)

                        group_name = f"{org.slug}:{role}"
                        group, _ = Group.objects.get_or_create(name=group_name)
                        user.groups.add(group)
                        user.save()

                    membership.save()

                print(f"Added membershipts {user_config.memberships} to user {user.username}")
            except Exception as e:
                self.stderr.write(f"Error creating/updating user {lokuser}: {e}")

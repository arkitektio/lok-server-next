
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.models import Organization, Role

class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        superusers = settings.SUPERUSERS

        # TODO: Implement validaiton of superusers

        for superuser in superusers:
            User = get_user_model()
            
            user = User.objects.filter(username=str(superuser["USERNAME"])).first()
            
            if not user:
                user = User.objects.create_superuser(
                    username=str(superuser["USERNAME"]),
                    email=str(superuser["EMAIL"]),
                    password=str(superuser["PASSWORD"]),
                )
            
                
                
            # Go through all orgnisations and add the admin role to the user
            for role in Role.objects.filter(identifier="admin").all():
                org = role.organization
                user.groups.add(role.group)
                self.stdout.write(f"Added admin role for {org.name} to user {user.username}")
            

            user.save()

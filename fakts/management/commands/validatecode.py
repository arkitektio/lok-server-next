from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from argparse import ArgumentParser
from karakter.models import Organization, Membership
from fakts.models import DeviceCode
from fakts.logic import validate_device_code

User = get_user_model()


class Command(BaseCommand):
    help = "Validate a device code for a specific user and organization"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("device_code", type=str, help="The device code to validate")
        parser.add_argument("--user", type=str, required=True, help="User ID")
        parser.add_argument("--org", type=str, required=True, help="Organization ID")

    def handle(self, *args, **options):
        device_code = options["device_code"]
        username = options["user"]
        orgslug = options["org"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User with username {username} does not exist")

        try:
            org = Organization.objects.get(slug=orgslug)
        except Organization.DoesNotExist:
            raise CommandError(f"Organization with slug {orgslug} does not exist")

        # check membership
        try:
            membership = Membership.objects.get(user=user, organization=org)
        except Membership.DoesNotExist:
            raise CommandError(f"User {user.username} is not a member of organization {org.name}")

        try:
            validate_device_code(literal_device_code=device_code, user=user, org=org)
        except Exception as e:
            raise CommandError(f"Failed to validate device code {device_code}: {str(e)}")

        print(f"Device code {device_code} is now valid for user {user.username} in organization {org.name}")

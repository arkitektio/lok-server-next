from .models import Organization, Role
from django.contrib.auth.models import Group


def create_role(organization: Organization, identifier: str):
    """
    Create a role for the organization with the given identifier.
    """
    group_name = f"{organization.identifier}:{identifier}"
    group, _ = Group.objects.get_or_create(name=group_name)
    role, _ = Role.objects.update_or_create(
        group=group,
        defaults={"organization": organization, "identifier": identifier}
    )
    return role

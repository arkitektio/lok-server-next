from .models import Organization, Role, Membership, User
from django.contrib.auth.models import Group


def create_role(organization: Organization, identifier: str):
    """
    Create a role for the organization with the given identifier.
    """
    group_name = f"{organization.identifier}:{identifier}"
    group, _ = Group.objects.get_or_create(name=group_name)
    role, _ = Role.objects.update_or_create(group=group, defaults={"organization": organization, "identifier": identifier})
    return role


def create_default_groups_for_org(org):
    for identifier in ["admin", "guest", "researcher"]:
        g, _ = Group.objects.get_or_create(name=f"{org.slug}:{identifier}")
        Role.objects.update_or_create(group=g, identifier=identifier, organization=org)


def add_user_roles(user: User, organization: Organization, roles: list[str]):
    """
    Make the given user an admin of the specified organization.
    """
    membership, _ = Membership.objects.update_or_create(
        user=user,
        organization=organization,
    )

    for srole in roles:
        role = Role.objects.get(organization=organization, identifier=srole)

        membership.roles.add(role)

        group_name = f"{organization.slug}:{srole}"
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        user.save()

    membership.save()

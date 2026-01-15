from .models import Organization, Role, Membership, User, Scope
from django.contrib.auth.models import Group


def create_role(organization: Organization, identifier: str):
    """
    Create a role for the organization with the given identifier.
    """
    role, _ = Role.objects.update_or_create(identifier=identifier, organization=organization)
    return role


def create_scope(organization: Organization, identifier: str):
    """
    Create a role for the organization with the given identifier.
    """
    role, _ = Scope.objects.update_or_create(identifier=identifier, organization=organization)
    return role


def create_default_roles_for_org(org: Organization):
    for identifier in ["admin", "guest", "user", "bot", "viewer", "editor", "contributor", "manager", "owner", "labeler"]:
        create_role(org, identifier)


def create_default_scopes_for_org(org: Organization):
    for identifier in ["openid", "profile", "email", "roles", "groups"]:
        create_scope(org, identifier)


def ensure_owner_is_admin(org: Organization):
    """
    Ensure that the admin user is added to the admin group of the organization.
    """
    membership, _ = Membership.objects.get_or_create(user=org.owner, organization=org)
    membership.roles.add(Role.objects.get(identifier="admin", organization=org))
    membership.save()


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

    membership.save()


def create_user_default_organization(user: User):
    """
    Create a default organization for the user upon signup.
    """
    org_slug = f"{user.username}-org"
    org, created = Organization.objects.get_or_create(
        slug=org_slug,
        defaults={
            "name": f"{user.username}'s Organization",
            "owner": user,
        },
    )

    if created:
        create_default_roles_for_org(org)

    add_user_roles(user, org, ["admin"])

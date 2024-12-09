from ekke.errors import EkkePermissionDenied
import time
from django.contrib.auth.models import Group
import logging
from ekke import structs
from typing import Any
from karakter.models import User
from oauth2_provider.models import Application


logger = logging.getLogger(__name__)


def token_to_username(token: structs.JWTToken):
    """Convert a JWT token to a username"""
    return f"{token.iss}_{token.sub}"


def set_user_groups(user: User, roles: list[str]):
    """Set the groups of a user"""
    for role in roles:
        g, _ = Group.objects.get_or_create(name=role)
        user.groups.add(g)


def expand_token(token: structs.JWTToken, force_client: bool = True) -> structs.Auth:
    if token.sub is None:
        raise EkkePermissionDenied("Missing sub parameter in JWT token")

    if token.iss is None:
        raise EkkePermissionDenied("Missing iss parameter in JWT token")

    if token.exp is None:
        raise EkkePermissionDenied("Missing exp parameter in JWT token")

    # Check if token is expired
    if token.exp < time.time():
        raise EkkePermissionDenied("Token has expired")

    if token.client_id is None:
        if force_client:
            raise EkkePermissionDenied("Missing client_id parameter in JWT token")

    try:
        if token.client_id is None:
            app = None
        else:
            app = Application.objects.get(client_id=token.client_id)

        user = User.objects.get(id=token.sub)

    except Exception as e:
        logger.error(f"Error while authenticating: {e}", exc_info=True)
        raise EkkePermissionDenied(f"Error while authenticating: {e}")

    return structs.Auth(
        token=token,
        user=user,
        app=app,
    )

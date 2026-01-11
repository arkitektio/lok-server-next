"""
authapp.token_generators

Implements a JWT Bearer token generator for the AuthorizationServer.

This module:
- Loads the signing key (RSA) from Django settings.
- Exposes a public JWK set via ``get_jwks`` used by token consumers to
  validate signatures.
- Adds application-specific claims (roles, preferred_username, sub,
  scope, active_org) to tokens emitted for clients/users.

Notes:
- The module intentionally exports only the public JWK (is_private=False)
  for inclusion in discovery endpoints; the private key is used for
  signing and must remain secret in settings.
"""

from authlib.oauth2.rfc9068 import JWTBearerTokenGenerator
from joserfc.jwk import RSAKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist

# Load RSA private key (used for signing). The settings.PRIVATE_KEY must
# contain the PEM-encoded private key string.
private_key = serialization.load_pem_private_key(settings.PRIVATE_KEY.encode("utf-8"), password=None, backend=default_backend())

# Generate a JWK representation from the private key. We expose the
# public part (is_private=False) as the published JWK set.
jwk = RSAKey.import_key(settings.PRIVATE_KEY)
jwk_dict = jwk.as_dict(is_private=False, kid="1")  # use True for full private JWK


class MyJWTBearerTokenGenerator(JWTBearerTokenGenerator):
    """Custom JWT Bearer token generator that adds application claims.

    The generator extends authlib's JWTBearerTokenGenerator and overrides
    a small set of hooks used during token creation.
    """

    def get_jwks(self) -> dict:
        """Return a JWK set (public keys) used by token consumers.

        Returns:
            dict: a JWK dictionary suitable for publishing as part of a
            JWKS endpoint.
        """
        return jwk_dict

    def get_extra_claims(self, client: Any, grant_type: Any, user: Any, scope: Optional[str]) -> dict:
        """Construct application-specific claims to include in the JWT.

        Behavior and assumptions:
        - If ``user`` is falsy (client credentials flows), the method
          attempts to use ``client.user`` as a fallback.
        - If ``scope`` is falsy, the client's stored scope is used.
        - Raises ValueError when required contextual data is missing.

        Returns a dict with keys:
        - roles: list of role identifiers the user has in the client's
                 organization
        - preferred_username: the user's username
        - sub: the user's id (subject)
        - scope: the resolved scope string
        - active_org: the client's organization slug
        """
        # actually resolve user and scope
        # user is actually a membership object
        membership = user

        if not membership:
            membership = client.client.membership

        if not scope:
            # fall back to the client's configured scope
            scope = client.scope

        if not membership:
            raise ValueError("Membership not found")

        if not membership:
            raise ValueError("User is not a member of the organization (anymore)")

        try:
            fakts_client = client.client
        except ObjectDoesNotExist:
            fakts_client = None

        # TODO: Implement correct scoping rules; for now expose roles and
        # some basic user identifiers used by resource servers.
        return {
            "roles": [role.identifier for role in membership.roles.all()],
            "preferred_username": membership.user.username,
            "sub": membership.user.id,
            "scope": scope,
            "active_org": membership.organization.slug,
            "client_app": fakts_client.release.app.identifier if fakts_client and fakts_client.release and fakts_client.release.app else None,
            "client_release": fakts_client.release.version if fakts_client and fakts_client.release else None,
            "client_device": fakts_client.node.node_id if fakts_client and fakts_client.node else None,
        }

    def get_audiences(self, client: Any, user: Any, scope: Optional[str]) -> str | list[str]:
        """Return the audience claim(s) for the token.

        The audience identifies intended recipients of the token. Return
        a list if there are multiple audiences.
        """
        return ["rekuest"]

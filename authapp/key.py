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

"""
authapp.server

Creates and configures the application's AuthorizationServer instance.

This module registers the supported grant types and the token
generator used to produce JWT bearer tokens. Other modules should import
``server`` and use its helpers (for example
``server.create_token_response``) to handle protocol endpoints.
"""

from authlib.integrations.django_oauth2 import AuthorizationServer
from .models import OAuth2Client, OAuth2Token
from .grants import ClientCredentialsGrant, AuthorizationCodeGrant, OpenIDCode
from .token_generators import MyJWTBearerTokenGenerator

# The AuthorizationServer is backed by the project's OAuth2Client and
# OAuth2Token models; these model classes implement the storage hooks
# required by authlib's integration layer.
server = AuthorizationServer(OAuth2Client, OAuth2Token)

# Register the project's supported grants. Add other grants here as
# needed (authorization_code, refresh_token, etc.).
server.register_grant(ClientCredentialsGrant)
server.register_grant(AuthorizationCodeGrant, [OpenIDCode(require_nonce=True)])
# Register a JWT bearer token generator under the default key. The
# generator is used to emit signed JWTs for access tokens.
server.register_token_generator(
    "default",
    MyJWTBearerTokenGenerator(issuer="lok"),
)

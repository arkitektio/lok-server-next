"""
authapp.server

Creates and configures the application's AuthorizationServer instance.

This module registers the supported grant types and the token
generator used to produce JWT bearer tokens. Other modules should import
``server`` and use its helpers (for example
``server.create_token_response``) to handle protocol endpoints.
"""

from django.conf import settings
from authlib.integrations.django_oauth2 import AuthorizationServer, BearerTokenValidator, ResourceProtector
from .models import OAuth2Client, OAuth2Token
from .grants import ClientCredentialsGrant, AuthorizationCodeGrant, OpenIDCode, RefreshTokenGrant
from .token_generators import MyJWTBearerTokenGenerator
from authlib.oidc.core import grants as oidcgrants, UserInfo
from .token_generators import jwk_dict
from authlib.oidc.core.userinfo import UserInfoEndpoint


from authlib.oauth2.rfc9068 import JWTBearerTokenGenerator, JWTBearerTokenValidator

# The AuthorizationServer is backed by the project's OAuth2Client and
# OAuth2Token models; these model classes implement the storage hooks
# required by authlib's integration layer.
server = AuthorizationServer(OAuth2Client, OAuth2Token)

# Register the project's supported grants. Add other grants here as
# needed (authorization_code, refresh_token, etc.).
server.register_grant(ClientCredentialsGrant)
server.register_grant(AuthorizationCodeGrant, [OpenIDCode(require_nonce=True)])
server.register_grant(RefreshTokenGrant)
# Register a JWT bearer token generator under the default key. The
# generator is used to emit signed JWTs for access tokens.


class MyUserInfoEndpoint(UserInfoEndpoint):
    def get_issuer(self):
        return settings.OIDC_ISSUER

    def generate_user_info(self, user, scope):
        return UserInfo(
            sub=user.id,
            name=user.name,
        )

    def resolve_private_key(self):
        return jwk_dict


class MyBearerTokenValidator(JWTBearerTokenValidator):
    def authenticate_token(self, token_string):
        return OAuth2Token.objects.get(access_token=token_string)

    def get_jwks(self) -> None:
        return jwk_dict


class Oauth2TokenValidator(BearerTokenValidator):
    pass


class RefreshTokenGenerator:
    def __call__(self, client, grant_type, user, scope):
        import secrets

        return secrets.token_urlsafe(48)


server.register_token_generator(
    "default",
    MyJWTBearerTokenGenerator(issuer=settings.OIDC_ISSUER, refresh_token_generator=RefreshTokenGenerator()),
)

resource_protector = ResourceProtector()
resource_protector.register_token_validator(Oauth2TokenValidator(OAuth2Token))
# server.register_endpoint(MyUserInfoEndpoint(server=server, resource_protector=resource_protector))

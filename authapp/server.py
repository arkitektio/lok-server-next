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
from fakts.models import Client
from .models import OAuth2Token
from .grants import AuthorizationCodeGrant, OpenIDCode, RefreshTokenGrant
from .fakts_grants import FaktsDeviceCodeGrant, FaktsRedeemGrant
from .token_generators import MyJWTBearerTokenGenerator
from authlib.oidc.core import UserInfo
from .token_generators import jwk_dict
from authlib.oidc.core.userinfo import UserInfoEndpoint


from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc9068 import JWTBearerTokenValidator

# The grant surface this server exposes, as advertised by every discovery
# document (/.well-known/fakts, /.well-known/oauth-authorization-server,
# /.well-known/openid-configuration). Keep in sync with the register_grant
# calls below.
GRANT_TYPES_SUPPORTED = [
    "authorization_code",
    "refresh_token",
    "urn:ietf:params:oauth:grant-type:device_code",
    "urn:fakts:grant-type:redeem",
]

# `none` is how the dynamically registered public fakts clients authenticate
# (client_id only); the secret methods serve confidential OIDC relying parties.
TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED = ["client_secret_basic", "client_secret_post", "none"]

# The AuthorizationServer is backed by the unified fakts Client (which
# implements authlib's ClientMixin directly) and OAuth2Token.
server = AuthorizationServer(Client, OAuth2Token)

# Register the project's supported grants.
#
# ClientCredentialsGrant is deliberately NOT registered: fakts clients use the
# device-code/redeem grants and the OIDC relying parties use authorization_code
# — nothing in the deployment exchanges client credentials, so the grant would
# only widen the attack surface of every confidential client's secret. The
# class is kept in grants.py for easy re-enable if a machine-to-machine
# integration ever needs it.
#
# PKCE (RFC 7636), required=True: authlib enforces the verifier for *public*
# clients (auth method `none`) only, so confidential relying parties are
# unaffected while authorization-code interception is closed for everyone
# without a client secret. The kontrol consent page posts through the real
# /o/authorize/ endpoint, which passes challenges through to the stored code.
server.register_grant(AuthorizationCodeGrant, [OpenIDCode(require_nonce=True), CodeChallenge(required=True)])
server.register_grant(RefreshTokenGrant)

# The canonical fakts grants: RFC 8628 device-code (interactive, approved in the
# kontrol frontend) and the headless redeem grant. Both issue the combined
# response — access token + refresh token + rendered service instances — for
# dynamically registered public clients. See authapp/fakts_grants.py.
server.register_grant(FaktsDeviceCodeGrant)
server.register_grant(FaktsRedeemGrant)

# RFC 7009 token revocation, served at /o/revoke/.
from .revocation import MyRevocationEndpoint  # noqa: E402  (needs `server` grants above conceptually grouped)

server.register_endpoint(MyRevocationEndpoint)
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


# Access-token lifetime, in seconds.
#
# Without an explicit generator authlib falls back to its own defaults
# (rfc6750/token.py: GRANT_TYPES_EXPIRES_IN), which are **864000 seconds — ten
# days** for both `authorization_code` and `client_credentials`, the two grants
# lok actually issues. That is the whole exposure window for a leaked token,
# because token verification on the consuming side is pure-JWT: it never reads
# the database, so `OAuth2Token.revoked` is not consulted and revocation has no
# effect outside `/o/user_info/`. Expiry is therefore the only control, and ten
# days is far too long for one.
#
# One hour matches the id_token's `exp` (authapp/grants.py) and leaves refresh
# tokens (30 days, `OAuth2Token.is_refresh_token_active`) to provide continuity —
# and those *are* revocable, since the refresh grant does hit the database.
ACCESS_TOKEN_EXPIRES_IN = 3600


def access_token_expires_in(client, grant_type) -> int:
    """Uniform access-token lifetime across every grant."""
    return ACCESS_TOKEN_EXPIRES_IN


server.register_token_generator(
    "default",
    MyJWTBearerTokenGenerator(
        issuer=settings.OIDC_ISSUER,
        refresh_token_generator=RefreshTokenGenerator(),
        expires_generator=access_token_expires_in,
    ),
)

resource_protector = ResourceProtector()
resource_protector.register_token_validator(Oauth2TokenValidator(OAuth2Token))
# server.register_endpoint(MyUserInfoEndpoint(server=server, resource_protector=resource_protector))

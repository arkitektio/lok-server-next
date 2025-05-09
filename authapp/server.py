from authlib.integrations.django_oauth2 import AuthorizationServer
from .models import OAuth2Client, OAuth2Token
from .grants import ClientCredentialsGrant
from .token_generators import MyJWTBearerTokenGenerator

server = AuthorizationServer(OAuth2Client, OAuth2Token)

server.register_grant(ClientCredentialsGrant)

server.register_token_generator(
    "default",
    MyJWTBearerTokenGenerator(
        issuer="lok"
    ),
)
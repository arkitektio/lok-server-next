from authlib.oauth2.rfc6749 import grants
from .models import OAuth2Client, OAuth2Token, AuthorizationCode
from authlib.oidc.core import grants as oidcgrants, UserInfo
from karakter.models import Membership
from django.conf import settings


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token: str) -> OAuth2Token | None:
        try:
            item = OAuth2Token.objects.get(refresh_token=refresh_token)
            if item.is_refresh_token_active():
                return item
        except OAuth2Token.DoesNotExist:
            return None

    def authenticate_user(self, credential):
        return credential.user

    def revoke_old_credential(self, credential):
        credential.revoked = True
        credential.save()


class OpenIDCode(oidcgrants.OpenIDCode):
    def exists_nonce(self, nonce, request):
        try:
            AuthorizationCode.objects.get(client_id=request.payload.client_id, nonce=nonce)
            return True
        except AuthorizationCode.DoesNotExist:
            return False

    def get_jwt_config(self, grant):
        return {
            "key": settings.PRIVATE_KEY,
            "alg": "RS256",
            "iss": "lok",
            "exp": 3600,
        }

    def generate_user_info(self, user: Membership, scope):
        # The user is actually a membership object (see token_generators.py)
        membership = user

        return UserInfo(
            sub=str(membership.user.id),
            name=membership.user.username,
            preferred_username=membership.user.username,
            active_org=membership.organization.slug,
            email=membership.user.email,
        )


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

    def query_authorization_code(self, code, client):
        try:
            item = AuthorizationCode.objects.get(code=code, client_id=client.client_id)
        except AuthorizationCode.DoesNotExist:
            return None

        if not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code: AuthorizationCode):
        authorization_code.delete()

    def authenticate_user(self, authorization_code: AuthorizationCode):
        return authorization_code.user

    def save_authorization_code(self, code: str, request):
        # openid request MAY have "nonce" parameter
        nonce = request.payload.data.get("nonce")
        client = request.client
        auth_code = AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.payload.scope,
            user=request.user,
            nonce=nonce,
        )
        auth_code.save()
        return auth_code

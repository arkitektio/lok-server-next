from authlib.oauth2.rfc6749 import grants
from .models import OAuth2Token, AuthorizationCode
from .oidc_claims import resolve_email, resolve_sub
from .fakts_grants import FaktsEnvelopeMixin
from authlib.oidc.core import grants as oidcgrants, UserInfo
from karakter.models import Membership
from django.conf import settings


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]


class OpenIDCode(oidcgrants.OpenIDCode):
    def exists_nonce(self, nonce, request):
        try:
            AuthorizationCode.objects.get(client_id=request.payload.client_id, nonce=nonce)
            return True
        except AuthorizationCode.DoesNotExist:
            return False

    def get_jwt_config(self, grant, client):
        # Implement key rotation and retrieval as needed
        return {
            "key": settings.PRIVATE_KEY,
            "alg": "RS256",
            "iss": settings.OIDC_ISSUER,
            "exp": 3600,
            "kid": settings.KEY_ID,
        }

    def encode_id_token(self, token, request):
        # generate_user_info() only receives (user, scope), but the per-client
        # `sub`/`email` policy lives on the client. Stash the client on the
        # per-request membership instance (request.user is a freshly loaded
        # Membership, so this is request-scoped and thread-safe).
        request.user._oauth_client = request.client
        return super().encode_id_token(token, request)

    def generate_user_info(self, user: Membership, scope):
        # The user is actually a membership object (see token_generators.py)
        membership = user
        client = getattr(membership, "_oauth_client", None)
        membership_is_subject = bool(getattr(client, "membership_is_subject", False))
        email_template = getattr(client, "email_template", None)

        return UserInfo(
            sub=resolve_sub(membership, membership_is_subject),
            name=membership.user.username,
            preferred_username=membership.user.username,
            active_org=membership.organization.slug,
            email=resolve_email(membership, email_template),
        )


class AuthorizationCodeGrant(FaktsEnvelopeMixin, grants.AuthorizationCodeGrant):
    # `none` lets *public* fakts clients (website kind, PKCE-protected) exchange
    # codes without a secret; confidential clients keep the secret methods. The
    # per-client gate is OAuth2Client.check_endpoint_auth_method.
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

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
            # The grant user *is* a Membership (the consent decision binds an
            # organization), and AuthorizationCode stores it as such.
            membership=request.user,
            nonce=nonce,
            # PKCE: persisted so `CodeChallenge` can require and verify a matching
            # `code_verifier` at token exchange. Empty when the client sent none.
            code_challenge=request.payload.data.get("code_challenge") or "",
            code_challenge_method=request.payload.data.get("code_challenge_method") or "",
        )
        auth_code.save()
        return auth_code

    def create_token_response(self):
        # Post-process with the fakts envelope so website-kind fakts clients
        # receive their instances through the standard code flow (this replaced
        # the org-less /f/retrieve/ handout). The id_token hook runs inside
        # super(), so appending afterwards is safe.
        status, token, headers = super().create_token_response()
        if status == 200:
            self.append_fakts_envelope(token)
        return status, token, headers


class RefreshTokenGrant(FaktsEnvelopeMixin, grants.RefreshTokenGrant):
    INCLUDE_NEW_REFRESH_TOKEN = True
    # `none` lets public fakts clients refresh with client_id + rotated refresh
    # token alone — for them the refresh chain *is* the credential. Confidential
    # clients still authenticate with their secret; the per-client gate is
    # OAuth2Client.check_endpoint_auth_method.
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

    def authenticate_refresh_token(self, refresh_token):
        # Guard *falsy*, not just None: authlib only rejects a missing
        # `refresh_token` parameter, so an empty string would otherwise reach
        # the lookup.
        if not refresh_token:
            return None
        try:
            item = OAuth2Token.objects.get(refresh_token=refresh_token)
            if item.is_refresh_token_active():
                return item
        except OAuth2Token.DoesNotExist:
            return None

    def authenticate_user(self, credential: OAuth2Token):
        return credential.user

    def revoke_old_credential(self, credential: OAuth2Token):
        credential.revoked = True
        credential.save()

    def create_token_response(self):
        # Post-process the standard response: carry the chain start through
        # rotation (so the absolute refresh-chain cap in
        # OAuth2Token.is_refresh_token_active cannot be reset by refreshing),
        # then append the fakts envelope — a fakts client's hourly refresh
        # re-renders its instances (aliases are host-aware), so configuration
        # drift propagates without re-approval.
        status, token, headers = super().create_token_response()
        if status == 200:
            old_credential = self.request.refresh_token
            OAuth2Token.objects.filter(access_token=token["access_token"]).update(
                chain_started_at=old_credential.chain_started_at
            )
            self.append_fakts_envelope(token)
        return status, token, headers

import time
from django.db import models
from django.contrib.auth import get_user_model
from authlib.oauth2.rfc6749 import ClientMixin, TokenMixin, AuthorizationCodeMixin

from karakter.models import Membership

User = get_user_model()


def scope_to_list(scope):
    """Convert a space-separated scope string to a list."""
    if not scope:
        return []
    return [s.strip() for s in scope.split(" ")]


def list_to_scope(scope_list):
    """Convert a list of scopes to a space-separated string."""
    if not scope_list:
        return ""
    return " ".join(scope_list)


def generate_client_id() -> str:
    """Generate a unique client ID for the OAuth2 client."""
    # Implement your logic to generate a unique client ID
    import uuid

    return str(uuid.uuid4())


def generate_client_secret() -> str:
    """Generate a unique client secret for the OAuth2 client."""
    # Implement your logic to generate a unique client secret
    import secrets

    return secrets.token_urlsafe(32)


def now_timestamp():
    return int(time.time())


class OAuth2Client(models.Model, ClientMixin):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="oauth2_clients", null=True, blank=True)
    client_id = models.CharField(max_length=48, unique=True)
    client_secret = models.CharField(max_length=120)
    redirect_uris = models.TextField(blank=True)
    scope = models.TextField(blank=True, default="openid email profile")
    token_endpoint_auth_method = models.CharField(max_length=48, default="client_secret_post")
    grant_types = models.TextField(default="authorization_code refresh_token client_credentials")
    response_types = models.TextField(blank=True)
    id_token_signed_response_alg = models.CharField(max_length=48, default="RS256")

    @property
    def user_id(self):
        """Return the membership associated with this authorization code."""
        if not self.client:
            raise ValueError("This is a bug in the logic of this server, we better fix it")
        return self.client.membership.id

    def __str__(self):
        return f"{self.client_id}"

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.default_redirect_uri

    def get_allowed_scope(self, scope):
        if not scope:
            return ""
        allowed = set(scope_to_list(self.scope))
        return list_to_scope([s for s in scope.split() if s in allowed])

    def check_redirect_uri(self, redirect_uri):
        return True  # TODO: implement proper check when
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == "token":
            if method == "client_secret_basic":
                return True
            if method == "client_secret_post":
                return True

            raise ValueError(f"Invalid endpoint for {method}")

        return self.token_endpoint_auth_method == method

        # TODO: developers can update this check method
        return True

    def check_response_type(self, response_type):
        allowed = self.response_type.split()
        return response_type in allowed

    def check_grant_type(self, grant_type):
        if grant_type == "client_credentials":
            return True

        if grant_type == "refresh_token":
            return True

        if grant_type == "authorization_code":
            return True

        raise ValueError(f"Invalid grant type: {grant_type}")
        allowed = self.grant_type.split()
        return grant_type in allowed


class OAuth2Token(models.Model, TokenMixin):
    """Model representing an OAuth2 token."""

    user = models.ForeignKey(Membership, on_delete=models.CASCADE)  # membership
    client_id = models.CharField(max_length=48, db_index=True)
    token_type = models.CharField(max_length=40)
    access_token = models.CharField(max_length=10000, unique=True, null=False)
    refresh_token = models.CharField(max_length=10000, db_index=True)
    scope = models.TextField(default="")
    revoked = models.BooleanField(default=False)
    issued_at = models.IntegerField(null=False, default=now_timestamp)
    expires_in = models.IntegerField(null=False, default=0)

    def check_client(self, client):
        return self.client_id == client.client_id

    def get_client_id(self):
        return self.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in

    def validate(self):
        if self.revoked:
            return False
        if self.get_expires_at() < now_timestamp():
            return False
        return True

    def is_refresh_token_active(self) -> bool:
        if self.revoked:
            return False
        # Assuming refresh tokens expire in 30 days (2592000 seconds)
        refresh_token_lifetime = 2592000
        if self.issued_at + refresh_token_lifetime < now_timestamp():
            return False
        return True

    def is_revoked(self) -> bool:
        return self.revoked

    def is_expired(self) -> bool:
        return self.get_expires_at() < now_timestamp()

    def get(self, key: str, default=None):
        return getattr(self, key, default)


class AuthorizationCode(models.Model, AuthorizationCodeMixin):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=48, db_index=True)
    code = models.CharField(max_length=120, unique=True, null=False)
    redirect_uri = models.TextField(default="", null=True)
    response_type = models.TextField(default="")
    scope = models.TextField(default="", null=True)
    auth_time = models.IntegerField(null=False, default=now_timestamp)

    # add nonce
    nonce = models.CharField(max_length=120, default="", null=True)
    # ... other fields and methods ...

    @property
    def user(self):
        """Return the membership associated with this authorization code."""
        return self.membership

    def is_expired(self):
        # Authorization code is valid for 10 minutes
        expiration_time = self.auth_time + 600
        return now_timestamp() > expiration_time

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope or ""

    def get_auth_time(self):
        return self.auth_time

    def get_nonce(self):
        return self.nonce

    def get_acr(self):
        return "1"  # Authentication Context Class Reference (check what this should be)

    def get_amr(self):
        return ["pwd"]  # Authentication Methods References (check what this should be)

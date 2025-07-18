import time
from django.db import models
from django.contrib.auth import get_user_model
from authlib.oauth2.rfc6749 import ClientMixin, TokenMixin

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey("karakter.Organization", on_delete=models.CASCADE, related_name="oauth2_clients")
    client_id = models.CharField(max_length=48, unique=True)
    client_secret = models.CharField(max_length=120)
    redirect_uris = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    token_endpoint_auth_method = models.CharField(max_length=48, default="client_secret_post")
    grant_types = models.TextField()
    response_types = models.TextField(blank=True)
    
    
    def __str__(self):
        return f"{self.client_id} ({self.user.username} @ {self.organization.slug})"

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
        if redirect_uri == self.default_redirect_uri:
            return True
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

        raise ValueError(f"Invalid grant type: {grant_type}")

        allowed = self.grant_type.split()
        return grant_type in allowed


class OAuth2Token(models.Model, TokenMixin):
    """Model representing an OAuth2 token."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=48, db_index=True)
    token_type = models.CharField(max_length=40)
    access_token = models.CharField(max_length=10000, unique=True, null=False)
    refresh_token = models.CharField(max_length=10000, db_index=True)
    scope = models.TextField(default="")
    revoked = models.BooleanField(default=False)
    issued_at = models.IntegerField(null=False, default=now_timestamp)
    expires_in = models.IntegerField(null=False, default=0)

    def get_client_id(self):
        return self.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in

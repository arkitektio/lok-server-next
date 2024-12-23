import logging
import dataclasses
from django.contrib.auth import get_user_model
from oauth2_provider.models import Application
from karakter.models import User
from pydantic import BaseModel, validator, Field

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class JWTToken(BaseModel):
    """The JWT Token that is used to authenticate users.
    This is a pydantic model that is used to validate the token."""

    sub: str
    iss: str
    exp: int
    client_id: str
    preferred_username: str
    roles: list[str]
    scope: str

    aud: str | None = None

    @validator("sub", pre=True)
    def sub_to_username(cls, v):
        if isinstance(v, int):
            return str(v)
        return v

    @property
    def changed_hash(self) -> str:
        return str(hash(self.sub + self.preferred_username + " ".join(self.roles)))

    @property
    def scopes(self) -> list[str]:
        return self.scope.split(" ")

    class Config:
        extra = "ignore"


class EkkeSettings(BaseModel):
    algorithms: list[str]
    public_key: str
    force_client: bool
    allow_imitate: bool
    imitate_headers: list[str] = Field(default_factory=lambda: ["X-Imitate-User"])
    authorization_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "X-Authorization", "AUTHORIZATION"]
    )
    imitate_permission: str = "ekke.imitate"


@dataclasses.dataclass
class Auth:
    """
    Mimics the structure of `AbstractAccessToken` so you can use standard
    Django Oauth Toolkit permissions like `TokenHasScope`.
    """

    token: JWTToken
    user: User
    app: Application

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.
        :param scopes: An iterable containing the scopes to check or None
        """
        return not self.is_expired() and self.allow_scopes(scopes)

    def is_expired(self):
        """
        Check token expiration with timezone awareness
        """
        # Token expiration is already checked
        return False

    def has_scopes(self, scopes):
        """
        Check if the token allows the provided scopes
        :param scopes: An iterable containing the scopes to check
        """

        provided_scopes = set(self.token.scopes)
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

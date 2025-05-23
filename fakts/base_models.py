from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Union
from django.conf import settings
from enum import Enum
from fakts import enums
from typing import Literal


class Layer(BaseModel):
    identifier: str
    kind: Union[Literal["WEB"], Literal["TAILSCALE"]]
    dns_probe: str | None = None
    get_probe: str | None = None



class WellKnownFakts(BaseModel):
    name: str =  settings.DEPLOYMENT_NAME
    version: str
    description: str | None = None
    claim: str
    base_url: str
    ca_crt: str | None = None
    layers: List[Layer] = Field(default_factory=list)


class Requirement(BaseModel):
    key: str
    service: str
    """ The service is the service that will be used to fill the key, it will be used to find the correct instance. It needs to fullfill
    the reverse domain naming scheme"""
    optional: bool = False
    """ The optional flag indicates if the requirement is optional or not. Users should be able to use the client even if the requirement is not met. """
    description: Optional[str] = None
    """ The description is a human readable description of the requirement. Will be show to the user when asking for the requirement."""


class Manifest(BaseModel):
    """A Manifest is a description of a client. It contains all the information
    necessary to create a set of client, release and app objects in the database.
    """

    identifier: str
    """ The identifier is a unique string that identifies the client. """
    version: str
    """ The version is a string that identifies the version of the client. """
    logo: Optional[str] = None
    """ The logo is a url to a logo that should be used for the client. """
    scopes: Optional[list[str]] = Field(default_factory=list)
    """ The scopes are a list of scopes that the client can request. """
    requirements: Optional[List[Requirement]] = Field(default_factory=list)
    """ The requirements are a list of requirements that the client needs to run on (e.g. needs GPU)"""


class CompositionInputModel(BaseModel):
    """A composition is a Jinja2 YAML template that will be rendered
    with the LinkingContext as context. The result of the rendering
    will be used to send to the client as a configuration."""

    name: str
    template: str




class DeviceCodeStartRequest(BaseModel):
    """A DeviceCodeStartRequest is used to start the device code flow. It contains
    the manifest of the client that wants to start the flow and the redirect uris
    as well as the requested client kind."""

    manifest: Manifest
    expiration_time_seconds: int = 300
    redirect_uris: list[str] = Field(default_factory=list)
    requested_client_kind: enums.ClientKindVanilla = enums.ClientKindVanilla.DEVELOPMENT
    request_public: bool = False
    supported_layers: List[str] = Field(default_factory=lambda: ["web"])


class ReedeemTokenRequest(BaseModel):
    """A RedeemTokenRequest is used to redeem a token for a development client. It only contains the token."""

    token: str
    manifest: Manifest
    supported_layers: List[str] = Field(default_factory=lambda: ["web"])



class DeviceCodeChallengeRequest(BaseModel):
    """A DeviceCodeChallengeRequest is used to start the device code flow. It only
    contains the device code."""

    code: str


class ConfigurationRequest(BaseModel):
    grant: enums.FaktsGrantKind
    device_code: Optional[str] = None


class ClaimRequest(BaseModel):
    token: str
    composition: Optional[str] = None
    requirements: Optional[list[Requirement]] = Field(default_factory=list)
    secure: bool = False


class RetrieveRequest(BaseModel):
    manifest: Manifest
    redirect_uris: list[str] = Field(default_factory=list)


class LinkingRequest(BaseModel):
    host: str
    port: Optional[str] = None
    is_secure: bool = False


class LinkingClient(BaseModel):
    authorization_grant_type: str
    client_type: str
    client_id: str
    client_secret: str
    name: str


class LinkingContext(BaseModel):
    deployment_name: str = Field(default=settings.DEPLOYMENT_NAME)
    request: LinkingRequest
    "Everything is a string"
    manifest: Manifest
    client: LinkingClient
    secure: bool = False


class ClientConfig(BaseModel):
    kind: enums.ClientKindVanilla
    token: str
    tenant: str

    def get_tenant(self):
        from django.contrib.auth import get_user_model

        try:
            return get_user_model().objects.get(username=self.tenant)
        except get_user_model().DoesNotExist:
            raise ValueError(
                f"Tenant {self.tenant} does not exist. Please create them first"
            )


class DevelopmentClientConfig(ClientConfig):
    kind: Literal["development"]
    user: str

    def get_user(self):
        from django.contrib.auth import get_user_model

        try:
            return get_user_model().objects.get(username=self.user)
        except get_user_model().DoesNotExist:
            raise ValueError(
                f"User {self.user} does not exist. Please create them first"
            )


class DesktopClientConfig(ClientConfig):
    kind: Literal["desktop"]


class WebsiteClientConfig(ClientConfig):
    kind: Literal["website"]
    tenant: str
    redirect_uris: List[str]
    public: bool = False


ClientUnion = WebsiteClientConfig | DesktopClientConfig | DevelopmentClientConfig


class AppConfig(Manifest):
    clients: list[ClientUnion]

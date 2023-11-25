from pydantic import BaseModel, Field, validator
from typing import List, Optional
from django.conf import settings
from enum import Enum
from fakts import enums, validators
from typing import Literal

class Manifest(BaseModel):
    """ A Manifest is a description of a client. It contains all the information
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
    requirements: Optional[list[str]] = Field(default_factory=list)
    """ The requirements are a list of requirements that the client needs to run on (e.g. needs GPU)"""




class CompositionInputModel(BaseModel):
    """ A composition is a Jinja2 YAML template that will be rendered 
    with the LinkingContext as context. The result of the rendering
    will be used to send to the client as a configuration."""
    name: str
    template: str

    @validator("template")
    def validate_template(cls, v):
        return validators.jinja2_yaml_template_validator(v)








class DeviceCodeStartRequest(BaseModel):
    """ A DeviceCodeStartRequest is used to start the device code flow. It contains
    the manifest of the client that wants to start the flow and the redirect uris
    as well as the requested client kind."""
    manifest: Manifest
    expiration_time_seconds: int = 300
    redirect_uris: list[str] = Field(default_factory=list) 
    requested_client_kind: enums.ClientKind = enums.ClientKind.DEVELOPMENT


class DeviceCodeChallengeRequest(BaseModel):
    """ A DeviceCodeChallengeRequest is used to start the device code flow. It only 
    contains the device code."""
    code: str


class ConfigurationRequest(BaseModel):
    
    grant: enums.FaktsGrantKind
    device_code: Optional[str] = None



class ClaimRequest(BaseModel):
    token: str
    composition: Optional[str] = None



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













class ClientConfig(BaseModel):
    kind: enums.ClientKind
    composition: str
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
        
    def get_composition(self):
        from .models import Composition

        try:
            return Composition.objects.get(name=self.composition)
        except Composition.DoesNotExist:
            raise ValueError(
                f"Composition {self.composition} does not exist. Please create it first"
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

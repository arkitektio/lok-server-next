from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal


class LayerModel(BaseModel):
    """Model representing a layer in the system."""

    identifier: str
    name: Optional[str] = None
    kind: Literal["loopback", "lan", "tailscale", "vpn", "public", "docker", "kubernetes", "tor", "zerotier", "manual", "proxy", "web"]
    logo: Optional[str] = None
    description: Optional[str] = "No description available"
    get_probe: Optional[str] = None


class AliasModel(BaseModel):
    """Model representing an alias for a service instance."""

    layer: str
    "Layer identifier this alias belongs to."
    ssl: Optional[bool] = None
    """The ssl flag indicates if the alias is available over SSL or not."""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    kind: Optional[Literal["relative", "absolute"]] = "relative"
    challenge: str = Field(default="ht", description="A challenge url to verify the alias on the client. If it returns a 200 OK, the alias is valid. It can additionally return a JSON object with a `challenge` key that contains the challenge to be solved by the client.")


class RoleConfig(BaseModel):
    """Model representing a role assigned to a service instance."""

    identifier: str
    description: Optional[str] = None


class ScopeConfig(BaseModel):
    """Model representing a scope assigned to a service instance."""

    identifier: str
    description: Optional[str] = None


class ServiceInstanceModel(BaseModel):
    """Model representing a service instance. Belong its to a service and has multiple aliases."""

    organization: Optional[str] = None
    service: str
    version: Optional[str] = "1.0.0"
    identifier: str
    roles: List[RoleConfig] = []
    scopes: List[ScopeConfig] = []
    aliases: List[AliasModel]


class ClientInstanceModel(BaseModel):
    organization: Optional[str] = None
    client: str
    version: Optional[str] = "1.0.0"
    identifier: str


class CompositionsConfigModel(BaseModel):
    instances: List[ServiceInstanceModel] = []
    clients: List[ClientInstanceModel] = []
    name: str
    description: Optional[str] = None
    organization: str
    identifier: Optional[str] = None  # Using identifier as slug


class YamlConfigModel(BaseModel):
    """Model representing the YAML configuration."""

    compositions: List[CompositionsConfigModel] = []

    @model_validator(mode="after")
    def validate_args(self):
        return self




class Oauth2ClientModel(BaseModel):
    """Model representing an OAuth2 client."""
    client_id: str
    client_secret: str
    redirect_uris: List[str] = []
    scopes: List[str] = []



class KommunityPartnerModel(BaseModel):
    """Model representing a Kommunity partner."""
    name: str
    identifier: str
    auth_url: str
    website_url: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    oauth2: Oauth2ClientModel

class KommunityPartnerConfigModel(BaseModel):
    """Model representing the Kommunity YAML configuration."""

    partners: List[KommunityPartnerModel] = []

    @model_validator(mode="after")
    def validate_args(self):
        return self
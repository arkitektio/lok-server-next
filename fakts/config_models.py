from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal
from fakts import enums
from fakts.base_models import CompositionManifest, StagingAlias, Role, Scope


class LayerModel(BaseModel):
    """Model representing a layer in the system."""

    identifier: str
    name: Optional[str] = None
    kind: Literal["loopback", "lan", "tailscale", "vpn", "public", "docker", "kubernetes", "tor", "zerotier", "manual", "proxy", "web"]
    logo: Optional[str] = None
    description: Optional[str] = "No description available"
    get_probe: Optional[str] = None


# Alias for backwards compatibility - use StagingAlias from base_models
AliasModel = StagingAlias


# Alias for backwards compatibility - use Role from base_models  
RoleConfig = Role


# Alias for backwards compatibility - use Scope from base_models
ScopeConfig = Scope


class ServiceInstanceModel(BaseModel):
    """Model representing a service instance. Belongs to a service and has multiple aliases."""

    organization: Optional[str] = None
    service: str
    version: Optional[str] = "1.0.0"
    identifier: str
    roles: List[Role] = Field(default_factory=list)
    scopes: List[Scope] = Field(default_factory=list)
    aliases: List[StagingAlias] = Field(default_factory=list)


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
    auth_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    oauth2: Optional[Oauth2ClientModel] = None
    partner_kind: enums.PartnerKind = enums.PartnerKind.PREAUTHORIZED
    kommunity_kind: enums.KommunityKind = enums.KommunityKind.OPEN
    auto_configure: bool = False
    preconfigured_composition: Optional[CompositionManifest] = None
    

class KommunityPartnerConfigModel(BaseModel):
    """Model representing the Kommunity YAML configuration."""

    partners: List[KommunityPartnerModel] = []

    @model_validator(mode="after")
    def validate_args(self):
        return self
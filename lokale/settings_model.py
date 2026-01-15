from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field


class AdminSettings(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class DjangoSettings(BaseModel):
    secret_key: str = "changeme"
    admin: AdminSettings
    use_x_forwarded_host: bool = True
    debug: bool = False
    hosts: List[str] = ["*"]


class DeploymentSettings(BaseModel):
    name: str = "default"
    description: str = "A Basic Arkitekt Deployment"


class Layer(BaseModel):
    identifier: str
    kind: str
    steward: Optional[str] = None
    dns_probe: Optional[str] = None


class Alias(BaseModel):
    layer: str
    kind: str
    path: Optional[str] = None
    challenge: Optional[str] = None


class Instance(BaseModel):
    identifier: str
    service: str
    aliases: List[Alias] = Field(default_factory=list)


class S3Buckets(BaseModel):
    media: str


class S3Settings(BaseModel):
    access_key: str
    secret_key: str
    protocol: str
    host: str
    port: int
    region: str = "us-east-1"
    buckets: S3Buckets


class RedisSettings(BaseModel):
    host: str
    port: int


class DBSettings(BaseModel):
    engine: str
    db_name: str
    username: str
    password: str
    host: str
    port: int


class EmailSettings(BaseModel):
    host: str = "NOTSET"
    port: int = 587
    use_tls: bool = True
    user: str = "NOTSET"
    password: str = "NOTSET"
    email: str = "NOTSET"


class LokSettings(BaseModel):
    public_key: Optional[str] = None
    public_key_pem_file: Optional[str] = None
    key_type: str = "RS256"
    static_tokens: Dict[str, str] = Field(default_factory=dict)
    issuer: Optional[str] = None


class RedeemToken(BaseModel):
    token: str
    user: str
    organization: str


class Organization(BaseModel):
    identifier: str
    name: str
    description: Optional[str] = "Default Organization Description"


class Membership(BaseModel):
    organization: str
    roles: List[str]


class User(BaseModel):
    name: Optional[str] = None
    username: str
    password: str  # In plain text in config?
    active_organization: Optional[str] = None
    memberships: List[Membership] = Field(default_factory=list)


class Role(BaseModel):
    name: str
    identifier: str
    description: Optional[str] = None
    organization: Optional[str] = None


class LivekitSettings(BaseModel):
    api_key: str
    api_secret: str
    api_url: str


class Settings(BaseModel):
    django: DjangoSettings
    deployment: DeploymentSettings
    layers: List[Layer] = Field(default_factory=list)
    instances: List[Instance] = Field(default_factory=list)
    s3: S3Settings
    redis: RedisSettings
    redeem_tokens: List[RedeemToken] = Field(default_factory=list)
    ca_file: str = "/certs/ca.crt"
    lok: LokSettings = Field(default_factory=LokSettings)
    db: DBSettings
    email: Optional[EmailSettings] = None
    private_key: Optional[str] = None  # It seems to be mandatory in settings.py (conf.private_key)
    public_key: Optional[str] = None
    scopes: Dict[str, str] = Field(default_factory=dict)
    token_expire_seconds: int = 60 * 60 * 24
    allowed_redirect_uri_schemes: List[str] = ["http", "https", "tauri", "arkitekt", "exp", "orkestrator", "doks", "kranken"]
    csrf_trusted_origins: List[str] = ["http://localhost", "https://localhost", "http://localhost:300"]
    force_script_name: str = "lok"
    organizations: List[Organization] = Field(default_factory=list)
    users: List[User] = Field(default_factory=list)
    roles: List[Role] = Field(default_factory=list)
    system_messages: List[Dict[str, Any]] = Field(default_factory=list)
    apps: List[Any] = Field(default_factory=list)
    livekit: Optional[LivekitSettings] = None

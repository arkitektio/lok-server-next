"""Typed, fully-documented configuration schema for the **lok** service.

Owned by this service. Values resolve (highest precedence first) from init
kwargs, environment variables (nested via ``__`` — e.g. ``POSTGRES__PASSWORD``),
then the YAML file (the mount's ``config.yaml`` by default; override with
``ARKITEKT_CONFIG_FILE``). Secret fields have **no default**: loading fails fast
with a ``ValidationError`` if they are not supplied via config or environment.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from authentikate.base_models import AuthentikateSettings

_DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"
)


class AdminSettings(BaseModel):
    """Django superuser created on first boot."""

    username: str = Field(description="Superuser login name.")
    password: str = Field(description="Superuser password. Secret — must be set.")
    email: Optional[str] = Field(default=None, description="Superuser email address.")


class DjangoSettings(BaseModel):
    """Core Django framework settings."""

    secret_key: str = Field(description="Django SECRET_KEY for cryptographic signing. Secret — must be set.")
    debug: bool = Field(default=False, description="Enable Django debug mode (never in production).")
    hosts: List[str] = Field(default_factory=lambda: ["*"], description="ALLOWED_HOSTS entries.")
    use_x_forwarded_host: bool = Field(default=True, description="Trust the X-Forwarded-Host header behind a reverse proxy.")
    admin: AdminSettings = Field(description="Superuser provisioned on first boot.")
    csrf_trusted_origins: List[str] = Field(default_factory=lambda: ["http://localhost", "https://localhost"], description="CSRF_TRUSTED_ORIGINS for unsafe (POST) requests.")
    force_script_name: str = Field(default="", description="URL path prefix (FORCE_SCRIPT_NAME) this service is served under.")


class PostgresSettings(BaseModel):
    """PostgreSQL database connection (Django ``DATABASES['default']``)."""

    model_config = ConfigDict(extra="allow")

    engine: str = Field(default="django.db.backends.postgresql", description="Django database backend (PostgreSQL).")
    db_name: str = Field(description="Database name.")
    username: str = Field(description="Database user.")
    password: str = Field(description="Database password. Secret — must be set.")
    host: str = Field(description="Database host.")
    port: int = Field(default=5432, description="Database port.")


class RedisSettings(BaseModel):
    """Redis connection (channel layer / cache)."""

    model_config = ConfigDict(extra="allow")

    host: str = Field(description="Redis host.")
    port: int = Field(default=6379, description="Redis port.")


class LokSettings(BaseModel):
    """Lok identity-provider key material used by this service."""

    public_key: Optional[str] = Field(default=None, description="Lok public key (SSH/PEM) used to verify issued tokens.")
    public_key_pem_file: Optional[str] = Field(default=None, description="Path to a PEM file holding the Lok public key.")
    key_type: str = Field(default="RS256", description="JWT signing algorithm.")
    static_tokens: Dict[str, Any] = Field(default_factory=dict, description="Pre-shared static tokens (testing only).")
    issuer: Optional[str] = Field(default=None, description="Expected token issuer (the ``iss`` claim).")


class EmailSettings(BaseModel):
    """SMTP settings for outbound email (optional block)."""

    host: str = Field(default="NOTSET", description="SMTP server host.")
    port: int = Field(default=587, description="SMTP server port.")
    use_tls: bool = Field(default=True, description="Use STARTTLS.")
    user: str = Field(default="NOTSET", description="SMTP username.")
    password: str = Field(description="SMTP password. Secret — must be set when an email block is present.")
    email: str = Field(default="NOTSET", description="Default From address.")


class DeploymentSettings(BaseModel):
    """Human-facing deployment identity."""

    name: str = Field(default="default", description="Deployment name.")
    description: str = Field(default="A Basic Arkitekt Deployment", description="Deployment description.")


class IonscaleSettings(BaseModel):
    """Connection to an ionscale tailnet coordinator (optional block)."""

    model_config = ConfigDict(extra="allow")

    server_url: str = Field(description="Ionscale server URL.")
    admin_key: str = Field(description="Ionscale admin API key. Secret — must be set.")
    coord_url: str = Field(description="Public coordination URL advertised to clients.")
    repository: Optional[str] = Field(default=None, description="Dotted path to an IonscaleRepo factory (tests).")


class DatalayerBucket(BaseModel):
    """A single S3 bucket binding within the datalayer."""

    model_config = ConfigDict(extra="allow")

    bucket: str = Field(description="S3 bucket name.")


class DatalayerSettings(BaseModel):
    """S3 storage connection and buckets (the datalayer module; replaces the old top-level ``s3`` block)."""

    model_config = ConfigDict(extra="allow")

    access_key: str = Field(description="S3 access key. Secret — must be set.")
    secret_key: str = Field(description="S3 secret key. Secret — must be set.")
    host: Optional[str] = Field(default=None, description="S3 endpoint host.")
    port: Optional[int] = Field(default=None, description="S3 endpoint port.")
    protocol: str = Field(default="http", description="S3 endpoint protocol (http or https).")
    region: str = Field(default="us-east-1", description="S3 region name.")
    media: DatalayerBucket = Field(description="Bucket for media / general file storage. Required for this service.")
    zarr: Optional[DatalayerBucket] = Field(default=None, description="Bucket for Zarr arrays.")
    parquet: Optional[DatalayerBucket] = Field(default=None, description="Bucket for Parquet tables.")
    bigfile: Optional[DatalayerBucket] = Field(default=None, description="Bucket for large binary files.")


class Settings(BaseSettings):
    """Top-level, validated configuration for the lok service."""

    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")

    django: DjangoSettings = Field(description="Core Django settings.")
    postgres: PostgresSettings = Field(description="PostgreSQL connection.")
    redis: RedisSettings = Field(description="Redis connection.")
    lok: LokSettings = Field(default_factory=LokSettings, description="Lok IdP key material.")
    authentikate: AuthentikateSettings = Field(description="Token-verification config (authentikate).")
    datalayer: DatalayerSettings = Field(description="S3 storage connection and buckets.")
    deployment: DeploymentSettings = Field(default_factory=DeploymentSettings, description="Deployment identity.")
    email: Optional[EmailSettings] = Field(default=None, description="Optional SMTP settings for outbound email.")
    ionscale: Optional[IonscaleSettings] = Field(default=None, description="Optional ionscale coordinator connection.")
    private_key: str = Field(description="OIDC/OAuth2 RSA private signing key (PEM). Secret — must be set.")
    public_key: Optional[str] = Field(default=None, description="OIDC/OAuth2 RSA public key (PEM).")
    key_type: str = Field(default="RS256", description="OAuth2 JWT signing algorithm.")
    token_expire_seconds: int = Field(default=60 * 60 * 24, description="OAuth2 access-token lifetime (seconds).")
    oidc_issuer: str = Field(default="http://lok", description="OIDC issuer URL advertised by lok.")
    kontrol_frontend_url: str = Field(default="/", description="Frontend URL used for redirects.")
    scopes: Dict[str, str] = Field(default_factory=dict, description="OAuth2 scope name -> human description.")
    allowed_redirect_uri_schemes: List[str] = Field(default_factory=lambda: ["http", "https", "tauri", "arkitekt", "exp", "orkestrator", "doks", "kranken"], description="URI schemes permitted as OAuth2 redirect targets.")
    socialaccount_providers: Dict[str, Any] = Field(default_factory=dict, description="django-allauth social provider config.")
    organizations: List[Dict[str, Any]] = Field(default_factory=list, description="Organizations ensured on boot.")
    users: List[Dict[str, Any]] = Field(default_factory=list, description="Users ensured on boot.")
    memberships: List[Dict[str, Any]] = Field(default_factory=list, description="User/organization memberships ensured on boot.")
    roles: List[Dict[str, Any]] = Field(default_factory=list, description="Roles ensured on boot.")
    redeem_tokens: List[Dict[str, Any]] = Field(default_factory=list, description="Redeem tokens provisioned on boot.")
    kommunity_partners: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-authorized kommunity partner apps.")
    system_messages: List[Dict[str, Any]] = Field(default_factory=list, description="System messages shown to users.")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Precedence: explicit init kwargs > environment variables > YAML file.
        path = os.environ.get("ARKITEKT_CONFIG_FILE", _DEFAULT_CONFIG)
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=path),
            file_secret_settings,
        )

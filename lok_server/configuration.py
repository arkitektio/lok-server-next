"""Typed, fully-documented configuration schema for the **lok** service.

Owned by this service. Values resolve (highest precedence first) from init
kwargs, environment variables (nested via ``__`` — e.g. ``POSTGRES__PASSWORD``),
then the YAML file (the mount's ``config.yaml`` by default; override with
``ARKITEKT_CONFIG_FILE``). Secret fields have **no default**: loading fails fast
with a ``ValidationError`` if they are not supplied via config or environment.
"""

import os
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from authentikate.base_models import AuthentikateSettings

_DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")


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
    secure_proxy_ssl_header: bool = Field(default=True, description="Trust X-Forwarded-Proto to detect HTTPS behind a reverse proxy (SECURE_PROXY_SSL_HEADER). Disable when not behind a TLS-terminating proxy.")
    admin: AdminSettings = Field(description="Superuser provisioned on first boot.")
    csrf_trusted_origins: List[str] = Field(default_factory=lambda: ["http://localhost", "https://localhost"], description="CSRF_TRUSTED_ORIGINS for unsafe (POST) requests.")
    force_script_name: str = Field(default="", description="URL path prefix (FORCE_SCRIPT_NAME) this service is served under.")
    language_code: str = Field(default="en-us", description="Django LANGUAGE_CODE.")
    time_zone: str = Field(default="UTC", description="Django TIME_ZONE.")
    log_level: str = Field(default="INFO", description="Root logger level (e.g. DEBUG, INFO, WARNING).")


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
    channel_prefix: str = Field(default="lok", description="Key prefix for the channels_redis channel layer.")


class LokSettings(BaseModel):
    """Lok identity-provider key material used by this service."""

    public_key: Optional[str] = Field(default=None, description="Lok public key (SSH/PEM) used to verify issued tokens.")
    key_id: str = Field(default="lok-key-1", description="JWK `kid` advertised in the JWKS and stamped into issued token headers. Must match the kid configured for the lok issuer in consumers' authentikate settings.")
    static_tokens: Dict[str, Any] = Field(default_factory=dict, description="Pre-shared static tokens (testing only).")


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
    eager_init: bool = Field(default=False, description="Eagerly initialize the ionscale repo on boot (tests).")
    auto_create_mesh: bool = Field(
        default=True,
        description="Automatically provision the mesh for each new organization on creation. "
        "Requires ionscale to be configured; when disabled, meshes are only created on explicit opt-in.",
    )


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
    default_acl: str = Field(default="private", description="Default ACL applied to stored objects (AWS_DEFAULT_ACL).")
    querystring_expire: int = Field(default=3600, description="Presigned URL lifetime in seconds (AWS_QUERYSTRING_EXPIRE).")
    file_overwrite: bool = Field(default=False, description="Overwrite existing files on name collision (AWS_S3_FILE_OVERWRITE).")
    secure: Optional[bool] = Field(default=None, description="Use TLS for S3 (AWS_S3_USE_SSL/SECURE_URLS). When None, derived from protocol == 'https'.")
    media: DatalayerBucket = Field(description="Bucket for media / general file storage. Required for this service.")
    zarr: Optional[DatalayerBucket] = Field(default=None, description="Bucket for Zarr arrays.")
    parquet: Optional[DatalayerBucket] = Field(default=None, description="Bucket for Parquet tables.")
    bigfile: Optional[DatalayerBucket] = Field(default=None, description="Bucket for large binary files.")


class HeadlessFrontendUrls(BaseModel):
    """Single-page-app URLs allauth-headless points users at (the ``{key}`` placeholders are filled in by allauth)."""

    account_confirm_email: str = Field(
        default="http://localhost/account/verify-email/{key}",
        description="Email-verification link; {key} substituted by allauth. Set per deployment.",
    )
    account_reset_password_from_key: str = Field(
        default="http://localhost/account/password/reset/key/{key}",
        description="Password-reset link; {key} substituted by allauth. Set per deployment.",
    )
    account_signup: str = Field(
        default="http://localhost/account/signup",
        description="Signup page URL. Set per deployment.",
    )


class AccountSettings(BaseModel):
    """django-allauth account/MFA behavior."""

    email_verification: str = Field(default="none", description="ACCOUNT_EMAIL_VERIFICATION (none/optional/mandatory).")
    login_methods: List[Literal["username", "email", "phone"]] = Field(
        default_factory=lambda: ["username"],
        description="ACCOUNT_LOGIN_METHODS — the identifier(s) users may log in with. "
        "Set to ['email'] to enable login via email.",
    )
    signup_fields: Optional[List[str]] = Field(
        default=None,
        description="ACCOUNT_SIGNUP_FIELDS, e.g. ['email*', 'password1*', 'password2*'] "
        "('*' marks a required field). When null, derived from login_methods.",
    )
    login_by_code_enabled: bool = Field(default=True, description="Enable login by emailed code (ACCOUNT_LOGIN_BY_CODE_ENABLED).")
    mfa_trust_enabled: bool = Field(default=True, description="Allow trusted devices (MFA_TRUST_ENABLED).")
    headless_frontend_urls: HeadlessFrontendUrls = Field(default_factory=HeadlessFrontendUrls, description="SPA URLs for allauth-headless flows.")
    social_provider_apps: List[str] = Field(
        default_factory=lambda: ["allauth.socialaccount.providers.orcid", "allauth.socialaccount.providers.google"],
        description="allauth social provider apps appended to INSTALLED_APPS.",
    )

    @model_validator(mode="after")
    def _coherent_login_and_signup(self) -> "AccountSettings":
        """Keep login_methods and signup_fields coherent.

        When signup_fields is omitted, derive a sensible default from
        login_methods. When it is provided, ensure an email login isn't paired
        with a signup form that never asks for an email.
        """
        if self.signup_fields is None:
            fields: List[str] = []
            if "email" in self.login_methods:
                fields.append("email*")
            if "username" in self.login_methods:
                fields.append("username*")
            if "phone" in self.login_methods:
                fields.append("phone*")
            fields += ["password1*", "password2*"]
            self.signup_fields = fields
        elif "email" in self.login_methods and not any(
            f.rstrip("*") == "email" for f in self.signup_fields
        ):
            raise ValueError(
                "account.login_methods includes 'email' but account.signup_fields "
                "does not collect an email — add 'email*' so users can sign up."
            )
        return self


class OpenIDAppSettings(BaseModel):
    """An OIDC/OAuth2 client provisioned on boot (see the ``ensureopenid`` command)."""

    client_name: str = Field(description="Human-readable client name.")
    client_id: str = Field(description="OAuth2 client_id.")
    client_secret: str = Field(description="OAuth2 client secret. Override per deployment.")
    redirect_uris: List[str] = Field(default_factory=list, description="Allowed OAuth2 redirect URIs.")


class SocialAppConfig(BaseModel):
    """Credentials for one OAuth app of a social provider.

    Mirrors the ``APP`` dict django-allauth reads from
    ``SOCIALACCOUNT_PROVIDERS[<provider>]["APP"]`` (or each entry of ``APPS``);
    the field names match allauth's exactly (see
    ``allauth/socialaccount/adapter.py``).
    """

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(description="OAuth client id / consumer key issued by the provider.")
    secret: str = Field(default="", description="OAuth client secret. Secret — set per deployment.")
    key: str = Field(default="", description="Extra key a few providers require; usually blank.")
    name: Optional[str] = Field(default=None, description="Human-readable app name (defaults to the provider id).")
    provider_id: Optional[str] = Field(default=None, description="Sub-provider instance id (OpenID Connect / SAML).")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Provider-app-specific settings blob.")


class SocialProviderConfig(BaseModel):
    """One entry of ``SOCIALACCOUNT_PROVIDERS``, keyed by provider id (e.g. ``google``).

    The common keys are typed for editor help and validation; any
    provider-specific extras (e.g. ``FETCH_USERINFO``) are still accepted
    verbatim via ``extra="allow"``.
    """

    model_config = ConfigDict(extra="allow")

    APP: Optional[SocialAppConfig] = Field(default=None, description="A single OAuth app credential.")
    APPS: Optional[List[SocialAppConfig]] = Field(default=None, description="Multiple app credentials (rarely needed; use APP for one).")
    SCOPE: Optional[List[str]] = Field(default=None, description="OAuth scopes to request (e.g. ['profile', 'email']).")
    AUTH_PARAMS: Optional[Dict[str, Any]] = Field(default=None, description="Extra query params on the authorize request.")
    OAUTH_PKCE_ENABLED: Optional[bool] = Field(default=None, description="Enable PKCE where the provider supports it (recommended).")
    VERIFIED_EMAIL: Optional[bool] = Field(default=None, description="Treat emails from this provider as already verified.")
    EMAIL_AUTHENTICATION: Optional[bool] = Field(default=None, description="Match logins to existing accounts by email.")


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
    account: AccountSettings = Field(default_factory=AccountSettings, description="django-allauth account/MFA behavior.")
    email: Optional[EmailSettings] = Field(default=None, description="Optional SMTP settings for outbound email.")
    ionscale: Optional[IonscaleSettings] = Field(default=None, description="Optional ionscale coordinator connection.")
    private_key: str = Field(description="OIDC/OAuth2 RSA private signing key (PEM). Secret — must be set.")
    oidc_issuer: str = Field(default="http://lok", description="OIDC issuer URL advertised by lok.")
    kontrol_frontend_url: str = Field(default="/", description="Frontend URL used for redirects.")
    socialaccount_providers: Dict[str, SocialProviderConfig] = Field(
        default_factory=dict,
        description="django-allauth SOCIALACCOUNT_PROVIDERS, keyed by provider id (e.g. 'google'). "
        "The matching app must also be listed in account.social_provider_apps.",
    )
    organizations: List[Dict[str, Any]] = Field(default_factory=list, description="Organizations ensured on boot.")
    users: List[Dict[str, Any]] = Field(default_factory=list, description="Users ensured on boot.")
    memberships: List[Dict[str, Any]] = Field(default_factory=list, description="User/organization memberships ensured on boot.")
    redeem_tokens: List[Dict[str, Any]] = Field(default_factory=list, description="Redeem tokens provisioned on boot.")
    kommunity_partners: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-authorized kommunity partner apps.")
    system_messages: List[Dict[str, Any]] = Field(default_factory=list, description="System messages shown to users.")
    openid_apps: List[OpenIDAppSettings] = Field(default_factory=list, description="OIDC/OAuth2 clients provisioned on boot. Provided per deployment.")

    @model_validator(mode="after")
    def _mandatory_verification_needs_smtp(self) -> "Settings":
        """Mandatory email verification blocks *all* post-signup login, so it
        requires a working outbound mail path — fail fast if the SMTP block is
        missing rather than locking users out at runtime.

        Note: ``account.login_by_code_enabled`` has the same email dependency but
        is not hard-failed here — password login still works without it. Instead it
        is soft-disabled (effective value ``False``) when no ``email:`` block is
        present; see ``ACCOUNT_LOGIN_BY_CODE_ENABLED`` in settings.py and CONFIG.md."""
        if self.account.email_verification == "mandatory" and self.email is None:
            raise ValueError(
                "account.email_verification is 'mandatory' but no `email:` SMTP block "
                "is configured — verification mails can't be sent and users would be "
                "permanently locked out. Add an `email:` block or relax verification."
            )
        return self

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

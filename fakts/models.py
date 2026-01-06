from django.db import models
from typing import Dict, Any
from django.contrib.auth import get_user_model
from django_choices_field import TextChoicesField

# Create your models here.
from django.core.exceptions import ObjectDoesNotExist
from typing import List
from django.db.models import Q
import uuid
import _json
from typing import Optional
from fakts import fields, enums
from django.contrib.auth.models import AbstractUser, Group
from karakter.models import MediaStore, Organization
from django.conf import settings
from authapp.models import OAuth2Client
from fakts import base_models, errors


class Layer(models.Model):
    name = models.CharField(max_length=1000)
    identifier = fields.IdentifierField(unique=True)
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    description = models.TextField(default="No description available", null=True, blank=True)
    dns_probe = models.TextField(default="No probe available", null=True, blank=True)
    get_probe = models.TextField(default="No probe available", null=True, blank=True)
    kind = TextChoicesField(
        choices_enum=enums.LayerKindChoices,
        default=enums.LayerKindChoices.WEB.value,
        help_text="The kind of layer",
    )

    def __str__(self):
        return f"{self.identifier}"


class Service(models.Model):
    name = models.CharField(max_length=1000)
    identifier = fields.IdentifierField()
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    description = models.TextField(default="No description available", null=True, blank=True)

    def __str__(self):
        return f"{self.identifier}"

    def validate_instance(self, instance: Dict[str, Any]) -> List[str]:
        errors = []
        warnings = []

        if not instance.get("key"):
            errors.append("Instance does not contain a key")

        return errors + warnings


class ServiceRelease(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="releases")
    version = fields.VersionField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["service", "version"],
                name="Only one per service and version",
            )
        ]

    def __str__(self):
        return f"{self.service}:{self.version}"


class ServiceInstance(models.Model):
    release = models.ForeignKey(ServiceRelease, on_delete=models.CASCADE, related_name="instances")
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    instance_id = models.CharField(max_length=1000, default="default")
    steward = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="stewarded_instances",
        help_text="The user who is responsible for this instance. If null the admin is stewared by admin user.",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="service_instances",
        help_text="The organization that owns this instance. If null the instance is global.",
    )
    device = models.ForeignKey("ComputeNode", on_delete=models.CASCADE, null=True, blank=True)
    template = models.TextField()
    denied_users = models.ManyToManyField(get_user_model(), related_name="denied_instances")
    denied_groups = models.ManyToManyField(Group, related_name="denied_instances")
    allowed_users = models.ManyToManyField(get_user_model(), related_name="allowed_instances")
    allowed_groups = models.ManyToManyField(Group, related_name="allowed_instances")
    allowed_organizations = models.ManyToManyField(Organization, related_name="allowed_instances")
    public_key = models.TextField(null=True, blank=True, help_text="The public key of the instance, if applicable.")
    token = models.CharField(max_length=1000, unique=True, help_text="The token of the instance, used for authentication.")

    def __str__(self):
        return f"{self.release}:{self.instance_id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["release", "instance_id", "organization", "device"],
                name="Only one instance_id per release, organization and device and instance",
            )
        ]

    def render(self, context: base_models.LinkingContext) -> base_models.InstanceClaim:
        """Render all aliases of the instance into a list of URLs."""
        urls = []
        for alias in self.aliases.all():
            try:
                url = alias.to_url(context)
                urls.append(url)
            except AssertionError as e:
                raise errors.InstanceAliasNotFound(f"Error rendering alias {alias}: {str(e)}")

        return base_models.InstanceClaim(
            service=self.release.service.identifier,
            identifier=str(self.id),
            aliases=urls,
        )


class InstancePermission(models.Model):
    kind = models.CharField(
        max_length=10,
        choices=[(e.value, e.name) for e in enums.InstancePermissionKind],
        help_text="Allow or deny access",
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="instance_permissions")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="instance_permissions", null=True, blank=True)
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="permissions")


class InstanceAlias(models.Model):
    """An alias for a service instance. This is used to provide a more user-friendly name for the instance."""

    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name="aliases", null=True, blank=True)
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=1000, null=True, blank=True, help_text="The name of the alias")
    host = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="The host of the alias, if its a ABSOLUTE alias (e.g. 'example.com'). If not set, the alias is relative to the layer's domain.",
    )
    port = models.IntegerField(
        null=True,
        blank=True,
        help_text="The port of the alias",
    )
    kind = TextChoicesField(
        choices_enum=enums.AliasKindChoices,
        default=enums.AliasKindChoices.RELATIVE.value,
        help_text="The kind of alias. If relative, the alias is relative to the layer's domain. If absolute, the alias is an absolute URL.",
    )
    ssl = models.BooleanField(
        default=True,
        help_text="If the alias is available over SSL or not. If not set, the alias is assumed to be available over SSL.",
    )
    challenge = models.TextField(
        default="ht",
        help_text=""""A challenge URL to verify the alias on the client. If it returns a 200 OK, the alias is valid. It can additionally return a JSON object with a `challenge
        key that contains the challenge to be solved by the client.""",
    )
    path = models.CharField(max_length=1000, null=True, blank=True, help_text="The path of the alias,")

    class Meta:
        """Meta class for InstanceAlias model."""

        constraints = [
            models.UniqueConstraint(
                fields=["instance", "host", "port", "ssl", "path", "kind"],
                name="Only one alias per instance and name",
            )
        ]

    def to_url(self, linking: base_models.LinkingContext) -> base_models.Alias:
        """Convert the alias to a URL based on the linking context."""
        if self.kind == enums.AliasKindChoices.RELATIVE.value:
            # Relative alias, use the layer's domain
            return base_models.Alias(
                id=str(self.id),
                ssl=linking.request.is_secure,
                host=linking.request.host,
                port=self.port if self.port else linking.request.port,
                path=self.path,
                challenge=self.challenge,
            )
        else:
            return base_models.Alias(
                id=str(self.id),
                ssl=self.ssl,
                host=self.host,
                port=self.port,
                path=self.path,
                challenge=self.challenge,
            )

    def __str__(self) -> str:
        """String representation of the InstanceAlias model."""
        return f"{self.instance}@{self.layer}:{self.name}"


class RedeemToken(models.Model):
    """A redeem token is a token that can be used to redeem the rights to create
    a client. It is used to give the recipient the right to create a client.

    If the token is not redeemed within the expires_at time, it will be invalid.
    If the token has been redeemed, but the manifest has changed, the token will be invalid.


    """

    client = models.OneToOneField("Client", on_delete=models.CASCADE, related_name="redeemed_client", null=True)
    token = models.CharField(max_length=1000, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="issued_tokens")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="issued_tokens",
    )


class DeviceCode(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    client = models.ForeignKey("Client", on_delete=models.CASCADE, null=True)
    staging_kind = TextChoicesField(
        choices_enum=enums.ClientKindChoices,
        default=enums.ClientKindChoices.DEVELOPMENT.value,
        help_text="The kind of staging client",
    )
    staging_manifest = models.JSONField(default=dict)
    staging_logo = models.CharField(max_length=1000, null=True)
    staging_public = models.BooleanField(default=False)
    staging_redirect_uris = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    denied = models.BooleanField(default=False)
    supported_layers = models.ManyToManyField(Layer, related_name="staging_device_codes")

    @property
    def manifest_as_model(self) -> base_models.Manifest:
        return base_models.Manifest(**self.staging_manifest)


class ServiceDeviceCode(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=100, unique=True)
    challenge_code = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, null=True)
    staging_manifest = models.JSONField(default=dict)
    staging_aliases = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    denied = models.BooleanField(default=False)

    @property
    def manifest_as_model(self) -> base_models.ServiceManifest:
        return base_models.ServiceManifest(**self.staging_manifest)

    @property
    def aliases_as_models(self) -> List[base_models.StagingAlias]:
        return [base_models.StagingAlias(**alias) for alias in self.staging_aliases]


class App(models.Model):
    name = models.CharField(max_length=1000)
    identifier = fields.IdentifierField()
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.identifier}"


class Release(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="releases")
    version = fields.VersionField()
    is_latest = models.BooleanField(default=False)
    is_dev = models.BooleanField(default=False)
    name = models.CharField(max_length=1000)
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    scopes = models.JSONField(default=list)
    requirements = models.JSONField(default=dict)

    def is_latest(self):
        return self.app.releases.filter(is_latest=True).count() == 1

    def is_dev(self):
        return "dev" in self.version

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["app", "version"],
                name="Only one per app and version",
            )
        ]

    def __str__(self):
        return f"{self.app}:{self.version}"


class DeviceGroup(models.Model):
    name = models.CharField(max_length=1000)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="device_groups",
    )

    def __str__(self):
        return f"{self.name} ({self.organization})"


class ComputeNode(models.Model):
    node_id = models.CharField(max_length=1000)
    name = models.CharField(max_length=1000, null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="compute_nodes",
    )
    device_groups = models.ManyToManyField(DeviceGroup, related_name="compute_nodes", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["node_id", "organization"],
                name="Only one node_id per organization",
            ),
        ]


class Client(models.Model):
    functional: bool = models.BooleanField(default=True)
    name = models.CharField(max_length=1000, default="No name")
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="clients", null=True)
    oauth2_client = models.OneToOneField(OAuth2Client, on_delete=models.CASCADE, related_name="client")
    kind = TextChoicesField(
        choices_enum=enums.ClientKindChoices,
        default=enums.ClientKindChoices.DEVELOPMENT.value,
        help_text="The kind of transformation",
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="clients")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    redirect_uris = models.CharField(max_length=1000, default=" ")
    public = models.BooleanField(default=False)
    token = models.CharField(default=uuid.uuid4, unique=True, max_length=10000)
    node = models.ForeignKey(ComputeNode, null=True, related_name="clients", on_delete=models.SET_NULL)
    public_sources = models.JSONField(default=list)
    tenant = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="managed_clients")
    created_at = models.DateTimeField(auto_now_add=True)
    requirements_hash = models.CharField(max_length=1000, unique=False)
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    last_reported_at = models.DateTimeField(auto_now=True)
    manifest = models.JSONField(default=dict)
    scopes = models.ManyToManyField("karakter.Scope", related_name="clients", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["release", "user", "organization", "node"],
                name="Only one per release, user and organization",
            )
        ]

    def __str__(self) -> str:
        return f"{self.kind} Client for {self.release}"


class ServiceInstanceMapping(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="mappings")
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="mappings")
    key = models.CharField(max_length=1000)
    description = models.TextField(max_length=1000, null=True, blank=True)
    optional = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "client"],
                name="Only one instance per key and composition",
            )
        ]

    def __str__(self):
        return f"{self.key}:{self.instance}@{self.client}"


class UsedAlias(models.Model):
    """
    Docstring for UsedAlias
    """

    valid = models.BooleanField(default=True)
    alias = models.ForeignKey(InstanceAlias, on_delete=models.CASCADE, related_name="usages", null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="used_aliases")
    key = models.CharField(max_length=1000)
    reason = models.TextField(null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alias} used in {self.key} at {self.used_at}"

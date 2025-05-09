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
from karakter.models import MediaStore
from django.conf import settings
from authapp.models import OAuth2Client


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


class ServiceInstance(models.Model):
    backend = models.CharField(max_length=1000)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name="instances")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="instances")
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    identifier = models.CharField(max_length=1000)
    template = models.TextField()
    denied_users = models.ManyToManyField(get_user_model(), related_name="denied_instances")
    denied_groups = models.ManyToManyField(Group, related_name="denied_instances")
    allowed_users = models.ManyToManyField(get_user_model(), related_name="allowed_instances")
    allowed_groups = models.ManyToManyField(Group, related_name="allowed_instances")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["backend", "identifier"],
                name="Only one instance per backend and identifier",
            )
        ]

    def __str__(self):
        return f"{self.service}:{self.backend}:{self.identifier}"


class UserDefinedServiceInstance(models.Model):
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="user_definitions")
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="services")
    values = models.JSONField(default=list)


class InstanceConfig(models.Model):
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="configs")
    key = models.CharField(max_length=1000)
    value = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instance", "key"],
                name="Only one config per instance and key",
            )
        ]

    def __str__(self):
        return f"{self.key}:{self.instance}"


class RedeemToken(models.Model):
    """A redeem token is a token that can be used to redeed the rights to create
    a client. It is used to give the recipient the right to create a client.

    If the token is not redeemed within the expires_at time, it will be invalid.
    If the token has been redeemed, but the manifest has changed, the token will be invalid.


    """

    client = models.OneToOneField("Client", on_delete=models.CASCADE, related_name="redeemed_client", null=True)
    token = models.CharField(max_length=1000, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="issued_tokens")


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


class Client(models.Model):
    name = models.CharField(max_length=1000, default="No name")
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="clients", null=True)
    oauth2_client = models.OneToOneField(OAuth2Client, on_delete=models.CASCADE, related_name="client")
    kind = TextChoicesField(
        choices_enum=enums.ClientKindChoices,
        default=enums.ClientKindChoices.DEVELOPMENT.value,
        help_text="The kind of transformation",
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="clients")
    redirect_uris = models.CharField(max_length=1000, default=" ")
    public = models.BooleanField(default=False)
    token = models.CharField(default=uuid.uuid4, unique=True, max_length=10000)

    tenant = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="managed_clients")
    created_at = models.DateTimeField(auto_now_add=True)
    requirements_hash = models.CharField(max_length=1000, unique=False)
    logo = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["release", "user"],
                name="Only one per releast, tenankt and kind",
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

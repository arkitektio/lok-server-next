from django.db import models
from typing import Dict, Any
from django.contrib.auth import get_user_model
from oauth2_provider.generators import generate_client_id, generate_client_secret
from django_choices_field import TextChoicesField

# Create your models here.
from django.core.exceptions import ObjectDoesNotExist
from oauth2_provider.models import Application
from typing import List
from django.db.models import Q
import uuid
import _json
from typing import Optional
from fakts import fields, enums




class Service(models.Model):
    name = models.CharField(max_length=1000)
    identifier = fields.IdentifierField()
    logo = fields.S3ImageField()
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
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="instances")
    identifier = models.CharField(max_length=1000)
    template = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["backend", "identifier"],
                name="Only one instance per backend and identifier",
            )
        ]

    def __str__(self):
        return f"{self.service}:{self.backend}:{self.identifier}"
    


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
    

class Composition(models.Model):
    """A template for a configuration"""
    name = models.CharField(max_length=1000)
    description = models.TextField(max_length=1000, null=True, blank=True)
    errors = models.JSONField(default=list)
    warnings = models.JSONField(default=list)
    type = models.CharField(max_length=1000, default="arkitekt")
    requirements_hash = models.CharField(max_length=1000, unique=True)

    def __str__(self) -> str:
        return self.name
    


class ServiceInstanceMapping(models.Model):
    composition = models.ForeignKey(Composition, on_delete=models.CASCADE, related_name="mappings")
    instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name="mappings")
    key = models.CharField(max_length=1000)
    description= models.TextField(max_length=1000, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "composition"],
                name="Only one instance per key and composition",
            )
        ]

    def __str__(self):
        return f"{self.key}:{self.instance}@{self.composition}"     



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
    staging_logo = fields.S3ImageField()
    staging_public = models.BooleanField(default=False)
    staging_redirect_uris = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    denied = models.BooleanField(default=False)



class App(models.Model):
    name = models.CharField(max_length=1000)
    identifier = fields.IdentifierField()
    logo = fields.S3ImageField()


    def __str__(self):
        return f"{self.identifier}"


class Release(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="releases")
    version = fields.VersionField()
    is_latest = models.BooleanField(default=False)
    is_dev = models.BooleanField(default=False)
    name = models.CharField(max_length=1000)
    logo = fields.S3ImageField()
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
    composition = models.ForeignKey(
        Composition, on_delete=models.CASCADE, related_name="clients"
    )
    release = models.ForeignKey(
        Release, on_delete=models.CASCADE, related_name="clients", null=True
    )
    oauth2_client = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="client"
    )
    kind = TextChoicesField(
        choices_enum=enums.ClientKindChoices,
        default=enums.ClientKindChoices.DEVELOPMENT.value,
        help_text="The kind of transformation",
    )
    public = models.BooleanField(default=False)
    token = models.CharField(
        default=uuid.uuid4, unique=True, max_length=10000
    )  # the api token
    client_id = models.CharField(
        max_length=1000, unique=True, default=generate_client_id
    )
    client_secret = models.CharField(max_length=1000, default=generate_client_secret)

    tenant = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="managed_clients"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="clients", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["release", "user", "kind"],
                name="Only one per releast, tenankt and kind",
            )
        ]

    def __str__(self) -> str:
        return f"{self.kind} Client for {self.release}"

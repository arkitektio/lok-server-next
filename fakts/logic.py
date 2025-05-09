from fakts import base_models
from fakts import models, inputs, enums
import re
from string import Template
import yaml
from pydantic import BaseModel, Field
import re
from typing import Optional
from fakts import fields, errors
from django.http import HttpRequest
from uuid import uuid4
from fakts.backends.instances import registry as backend_registry
from fakts.base_models import Manifest
from hashlib import sha256
from django.conf import settings


def render_user_defined(instance: models.ServiceInstanceMapping, context: base_models.LinkingContext) -> dict:
    user_defined = models.UserDefinedServiceInstance.objects.filter(instance=instance).first()

    if user_defined is None:
        raise errors.ConfigurationError(f"No user defined instance found for {instance}")

    values = {}

    for value in user_defined.values:
        x = inputs.KeyValueInput(**value)

        value = Template(x.value).safe_substitute(context.dict())
        if x.as_type == enums.FaktValueType.STRING:
            values[x.key] = value
        elif x.as_type == enums.FaktValueType.INT:
            values[x.key] = int(value)
        elif x.as_type == enums.FaktValueType.FLOAT:
            values[x.key] = float(value)
        elif x.as_type == enums.FaktValueType.BOOL:
            values[x.key] = bool(value)

    return values


def render_composition(client: models.Client, context: base_models.LinkingContext) -> dict:
    config_dict = {}

    config_dict["self"] = {}
    config_dict["self"]["deployment_name"] = context.deployment_name

    for mapping in client.mappings.all():
        instance = mapping.instance

        if instance.backend == settings.USER_DEFINED_BACKEND_NAME:
            value = render_user_defined(instance, context)

            config_dict[mapping.key] = value
        else:
            if instance.backend not in backend_registry.backends:
                raise errors.BackendNotAvailable(f"The backend {instance.backend} for this instance is not available")

            backend = backend_registry.backends[instance.backend]

            try:
                value = backend.render(instance.identifier, context)
            except Exception as e:
                raise errors.BackendError(f"An error occurred while rendering the backend instance {instance}: {str(e)}") from e

            if not isinstance(value, dict):
                raise errors.ConfigurationError(f"The backend {instance.backend} for this instance did not return a dictionary")

            config_dict[mapping.key] = value

    return config_dict


def find_instance_for_requirement(service: models.Service, requirement: base_models.Requirement, supported_layers: list[models.Layer], user: models.AbstractUser) -> models.ServiceInstance:
    instance = (
        models.ServiceInstance.objects.filter(
            service=service,
            layer__in=supported_layers,
        )
        .filter(
            models.Q(allowed_users__isnull=True)
            | models.Q(allowed_users=user) & (models.Q(denied_users__isnull=True) | ~models.Q(denied_users=user)) & (models.Q(allowed_groups__isnull=True) | models.Q(allowed_groups__in=user.groups.all())) & (models.Q(denied_groups__isnull=True) | ~models.Q(denied_groups__in=user.groups.all()))
        )
        .first()
    )

    if instance is None:
        raise errors.InstanceNotFound(f"Instance {requirement.service} not acccessible for {user.username} through these layers: {','.join(map(str, supported_layers.all()))}. Please contact the administrator.")

    return instance


def hash_requirements(requirements: list[base_models.Requirement]) -> str:
    # Order the requirements by service and key and hash them
    return sha256(".".join(sorted([req.service + req.key for req in requirements])).encode()).hexdigest()


def auto_compose(client: models.Client, manifest: base_models.Manifest, supported_layers: list[models.Layer], user: models.AbstractUser) -> models.Client:
    requirements = manifest.requirements

    if hash_requirements(requirements) != client.requirements_hash:
        errors = []
        warnings = []

        for old_mapping in client.mappings.all():
            old_mapping.delete()

        for req in manifest.requirements:
            try:
                service = models.Service.objects.get(identifier=req.service)

                instance = find_instance_for_requirement(service, req, supported_layers, user)

                models.ServiceInstanceMapping.objects.get_or_create(
                    client=client,
                    instance=instance,
                    key=req.key,
                )

            except Exception as e:
                if req.optional:
                    warnings.append(str(e))
                else:
                    raise Exception(f"Unable to find instance for requirement {req.service}") from e

        client.requirements_hash = hash_requirements(requirements)
        client.save()

    return client


def check_compability(manifest: base_models.Manifest, supported_layers: list[models.Layer], user: models.AbstractUser) -> list[str] | list[str]:
    errors = []
    warnings = []

    for req in manifest.requirements:
        try:
            try:
                service = models.Service.objects.get(identifier=req.service)
            except models.Service.DoesNotExist:
                raise Exception(f"Service {req.service} is not registered on this server. Please contact the administrator to add this feature.")

            instance = find_instance_for_requirement(service, req, supported_layers, user)

        except Exception as e:
            if req.optional:
                warnings.append(str(e))
            else:
                errors.append(str(e))

    return errors, warnings


def create_api_token():
    return str(uuid4())


def create_device_code():
    return "".join([str(uuid4())[-1] for _ in range(8)])


def create_linking_context(request: HttpRequest, client: models.Client, claim: base_models.ClaimRequest) -> base_models.LinkingContext:
    host_string = request.get_host().split(":")
    if len(host_string) == 2:
        host = host_string[0]
        port = host_string[1]
    else:
        host = host_string[0]
        port = None

    return base_models.LinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            is_secure=request.is_secure(),
        ),
        secure=claim.secure,
        manifest=base_models.Manifest(
            identifier=client.release.app.identifier,
            version=client.release.version,
            scopes=client.release.scopes,
        ),
        client=base_models.LinkingClient(
            client_id=client.oauth2_client.client_id,
            client_secret=client.oauth2_client.client_secret,
            client_type="confidential",
            authorization_grant_type="client-credentials",
            name=client.name,
            redirect_uris=client.oauth2_client.redirect_uris.split(" "),
        ),
    )


def create_fake_linking_context(client: models.Client, host, port, secure=False) -> base_models.LinkingContext:
    return base_models.LinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            is_secure=secure,
        ),
        secure=secure,
        manifest=base_models.Manifest(
            identifier=client.release.app.identifier,
            version=client.release.version,
            scopes=client.release.scopes,
        ),
        client=base_models.LinkingClient(
            client_id=client.client_id,
            client_secret=client.client_secret,
            client_type=client.oauth2_client.client_type,
            authorization_grant_type=client.oauth2_client.authorization_grant_type,
            name=client.oauth2_client.name,
            redirect_uris=client.oauth2_client.redirect_uris.split(" "),
        ),
    )

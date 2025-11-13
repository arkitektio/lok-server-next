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
from fakts.base_models import Manifest, ClaimAnswer, InstanceClaim, SelfClaim, AuthClaim
from hashlib import sha256
from django.conf import settings
from typing import Dict


def render_composition(client: models.Client, context: base_models.LinkingContext) -> dict:
    config_dict = {}

    self_claim = SelfClaim(
        deployment_name=context.deployment_name,
    )

    auth_claim = AuthClaim(
        client_id=client.oauth2_client.client_id,
        client_secret=client.oauth2_client.client_secret,
        scopes=client.release.scopes,
        token_url=f"{context.request.base_url}/o/token/",
    )

    instances_map: Dict[str, InstanceClaim] = {}

    for mapping in client.mappings.all():
        instance: models.ServiceInstance = mapping.instance

        value = instance.render(context)
        instances_map[mapping.key] = value

    claim = ClaimAnswer(
        self=self_claim,
        auth=auth_claim,
        instances=instances_map,
    )

    return claim.model_dump()


def find_instance_for_requirement(service: models.Service, requirement: base_models.Requirement, user: models.AbstractUser) -> models.ServiceInstance:
    instance = (
        models.ServiceInstance.objects.filter(
            service=service,
        )
        .filter(
            models.Q(allowed_users__isnull=True)
            | models.Q(allowed_users=user) & (models.Q(denied_users__isnull=True) | ~models.Q(denied_users=user)) & (models.Q(allowed_groups__isnull=True) | models.Q(allowed_groups__in=user.groups.all())) & (models.Q(denied_groups__isnull=True) | ~models.Q(denied_groups__in=user.groups.all()))
        )
        .first()
    )

    if instance is None:
        raise errors.InstanceNotFound(f"Instance {requirement.service} not acccessible for {user.username}. Please contact the administrator.")

    return instance


def hash_requirements(requirements: list[base_models.Requirement]) -> str:
    # Order the requirements by service and key and hash them
    return sha256(".".join(sorted([req.service + req.key for req in requirements])).encode()).hexdigest()


def auto_compose(client: models.Client, manifest: base_models.Manifest, user: models.AbstractUser, node: models.ComputeNode | None = None) -> models.Client:
    requirements = manifest.requirements

    if not requirements:
        return client

    if hash_requirements(requirements) != client.requirements_hash:
        errors = []
        warnings = []

        for old_mapping in client.mappings.all():
            old_mapping.delete()

        for req in requirements:
            try:
                service = models.Service.objects.get(identifier=req.service)

                instance = find_instance_for_requirement(service, req, user)

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


def check_compability(manifest: base_models.Manifest, user: models.AbstractUser) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest.requirements:
        return errors, warnings

    for req in manifest.requirements:
        try:
            try:
                service = models.Service.objects.get(identifier=req.service)
            except models.Service.DoesNotExist:
                raise Exception(f"Service {req.service} is not registered on this server. Please contact the administrator to add this feature.")

            instance = find_instance_for_requirement(service, req, user)

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

    base_url = request.build_absolute_uri("/") + settings.MY_SCRIPT_NAME

    return base_models.LinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            base_url=base_url,
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


def validate_device_code(literal_device_code: str, user: models.AbstractUser, org: models.Organization) -> models.DeviceCode:
    from .builders import create_client

    try:
        device_code = models.DeviceCode.objects.get(
            code=literal_device_code,
        )
        if device_code.client:
            raise ValueError(f"Device code {literal_device_code} is already validated.")

        manifest = base_models.Manifest(**device_code.staging_manifest)

        redirect_uris = (" ".join(device_code.staging_redirect_uris),)

        client = models.Client.objects.filter(
            release__app__identifier=device_code.staging_manifest["identifier"],
            release__version=device_code.staging_manifest["version"],
            kind=device_code.staging_kind,
            tenant=user,
            organization=org,
            redirect_uris=redirect_uris,
        ).first()

        if not client:
            token = create_api_token()

            manifest = base_models.Manifest(**device_code.staging_manifest)
            config = None

            if device_code.staging_kind == enums.ClientKindVanilla.DEVELOPMENT.value:
                config = base_models.DevelopmentClientConfig(
                    kind=enums.ClientKindVanilla.DEVELOPMENT.value,
                    token=token,
                    user=user.username,
                    organization=org.slug,
                    tenant=user.username,
                )

            else:
                raise Exception("Unknown client kind or no longer supported")

            client = create_client(manifest=manifest, config=config, user=user)

        device_code.client = client
        device_code.save()
        return device_code
    except models.DeviceCode.DoesNotExist:
        raise ValueError(f"Device code {literal_device_code} does not exist or is invalid.")

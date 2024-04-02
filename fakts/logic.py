from fakts import base_models
from fakts import models
import re
from jinja2 import Template, TemplateSyntaxError, TemplateError
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


def render_composition(composition: models.Composition, context: base_models.LinkingContext) -> dict:

    config_dict = {}

    config_dict["self"] = {}
    config_dict["self"]["deployment_name"] = context.deployment_name


    for mapping in composition.mappings.all():

        instance = mapping.instance


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


def find_instance_for_requirement(service: models.Service, requirement: base_models.Requirement) -> models.ServiceInstance:

    instance = models.ServiceInstance.objects.filter(
        service=service,
    ).first()


    if instance is None:
        raise errors.InstanceNotFound(f"Instance {requirement.instance} not found for service {service.identifier}")

    return instance



def hash_requirements(requirements: dict[str, base_models.Requirement]) -> str:
    return sha256(".".join([key + req.service for key, req in requirements.items()]).encode()).hexdigest()


def auto_create_composition(manifest: base_models.Manifest) -> models.Composition:


    composition, _ = models.Composition.objects.get_or_create(
        requirements_hash=hash_requirements(manifest.requirements),
        defaults=dict(
            name=f"Auto created composition for {manifest.identifier}/{manifest.version}",
            type="auto",
        )
    )


    errors = []
    warnings = []

    for key, req in manifest.requirements.items():

        try:
            service = models.Service.objects.get(identifier=req.service)
        
            instance = find_instance_for_requirement(service, req)

            models.ServiceInstanceMapping.objects.create(
                composition=composition,
                instance=instance,
                key=key,
            )

        except Exception as e:
            if req.optional:
                warnings.append(str(e))
            else:
                errors.append(str(e))


    if len(errors) > 0:
        composition.valid = False
    else:
        composition.valid = True

    
    composition.errors = errors
    composition.warnings = warnings
    composition.save()

    return composition


def check_compability(manifest: base_models.Manifest) -> list[str] | list[str]:

    errors = []
    warnings = []

    for key, req in manifest.requirements.items():

        try:
            try:
                service = models.Service.objects.get(identifier=req.service)
            except models.Service.DoesNotExist:
               raise Exception(f"Service {req.service} not found on this server. Please contact the administrator.")
        
            instance = find_instance_for_requirement(service, req)

        except Exception as e:
            if req.optional:
                warnings.append(str(e))
            else:
                errors.append(str(e))


    return errors , warnings


def create_api_token():
    return str(uuid4())


def create_device_code():
    return "".join([str(uuid4())[-1] for _ in range(8)])


def create_linking_context(request: HttpRequest, client: models.Client) -> base_models.LinkingContext:
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




def create_fake_linking_context(client: models.Client, host, port, secure=False) -> base_models.LinkingContext:
    

    return base_models.LinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            is_secure=secure,
        ),
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






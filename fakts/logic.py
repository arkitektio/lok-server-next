from fakts import base_models
from karakter import models as karakter_models
from fakts import models, inputs, enums
from pydantic import BaseModel, Field
import re
from typing import Optional, Callable
from fakts import fields, errors
from django.http import HttpRequest
from uuid import uuid4, uuid5, NAMESPACE_DNS
from fakts.base_models import Alias, Manifest, ClaimAnswer, InstanceClaim, SelfClaim, AuthClaim, CompositionAuthClaim, CompositionInstanceClaim, CompositionClientClaim, CompositionClaimAnswer, CompositionManifest
from hashlib import sha256
from django.conf import settings
from typing import Dict
from ionscale.repo import django_repo


def create_composition_from_manifest(
    manifest: CompositionManifest,
    organization: karakter_models.Organization,
    creator: karakter_models.User,
    token: str | None = None,
    log: Callable[[str], None] | None = None,
) -> models.Composition:
    """
    Create a composition from a CompositionManifest for a given organization.
    
    This is the core logic for creating compositions with all their service instances,
    roles, scopes, and aliases.
    
    Args:
        manifest: The composition manifest containing the configuration
        organization: The organization to create the composition for
        creator: The user who will be the creator of the composition
        token: Optional token for the composition (generated if not provided)
        log: Optional logging function for progress messages
    
    Returns:
        The created or updated Composition instance
    """
    if not token:
        token = str(uuid5(NAMESPACE_DNS, f"{manifest.identifier}:{organization.slug}"))
    
    # Create or update the composition
    composition, created = models.Composition.objects.update_or_create(
        token=token,
        defaults={
            "name": manifest.identifier or "Unnamed Composition",
            "description": manifest.description or "Auto-configured composition",
            "organization": organization,
            "creator": creator,
        }
    )
    
    if log:
        log(f"{'Created' if created else 'Updated'} composition '{composition.name}' for org '{organization.slug}'")
    
    # Create service instances from the composition manifest
    for instance_request in manifest.instances:
        service_manifest = instance_request.manifest
        
        # Create or get the service
        service, _ = models.Service.objects.get_or_create(
            identifier=service_manifest.identifier,
            defaults={"name": service_manifest.identifier}
        )
        
        # Create or get the service release
        release, _ = models.ServiceRelease.objects.get_or_create(
            service=service,
            version=service_manifest.version
        )
        
        # Create or update the service instance
        instance, inst_created = models.ServiceInstance.objects.update_or_create(
            token=instance_request.identifier,
            defaults={
                "steward": creator,
                "release": release,
                "organization": organization,
                "template": "{}",
                "instance_id": instance_request.identifier,
                "composition": composition,
            }
        )
        
        if log:
            log(f"  {'Created' if inst_created else 'Updated'} instance: {instance.token}")
        
        # Create roles from manifest
        if service_manifest.roles:
            for role_config in service_manifest.roles:
                role, role_created = karakter_models.Role.objects.get_or_create(
                    organization=organization,
                    identifier=role_config.key,
                    defaults={
                        "description": role_config.description,
                        "creating_instance": instance
                    }
                )
                role.used_by.add(instance)
                if log:
                    log(f"    {'Created' if role_created else 'Updated'} role: {role.identifier}")
        
        # Create scopes from manifest
        if service_manifest.scopes:
            for scope_config in service_manifest.scopes:
                scope, scope_created = karakter_models.Scope.objects.get_or_create(
                    organization=organization,
                    identifier=scope_config.key,
                    defaults={
                        "description": scope_config.description,
                        "creating_instance": instance
                    }
                )
                scope.used_by.add(instance)
                if log:
                    log(f"    {'Created' if scope_created else 'Updated'} scope: {scope.identifier}")
        
        # Create aliases from staging aliases
        for alias in instance_request.aliases:
            alias_obj, alias_created = models.InstanceAlias.objects.update_or_create(
                instance=instance,
                name=alias.name or alias.id,
                defaults={
                    "host": alias.host,
                    "port": alias.port,
                    "ssl": alias.ssl if alias.ssl is not None else True,
                    "path": alias.path,
                    "kind": alias.kind,
                    "challenge": alias.challenge,
                }
            )
            if log:
                log(f"    {'Created' if alias_created else 'Updated'} alias: {alias_obj.name}")
    
    return composition


def create_composition_from_partner(
    partner: models.KommunityPartner,
    organization: karakter_models.Organization,
    creator: karakter_models.User,
    log: Callable[[str], None] | None = None,
) -> models.Composition | None:
    """
    Create a composition from a KommunityPartner's preconfigured_composition for a given organization.
    
    This is a convenience wrapper around create_composition_from_manifest that handles
    the partner-specific logic like generating deterministic tokens.
    
    Args:
        partner: The KommunityPartner with the preconfigured composition
        organization: The organization to create the composition for
        creator: The user who will be the creator of the composition
        log: Optional logging function for progress messages
    
    Returns:
        The created Composition or None if the partner has no preconfigured composition
    """
    manifest = partner.preconfigured_composition_as_model
    if not manifest:
        return None
    
    # Generate deterministic token from partner identifier and org slug
    token = str(uuid5(NAMESPACE_DNS, f"{partner.identifier}:{organization.slug}"))
    
    if log:
        log(f"Creating composition from partner '{partner.identifier}'")
    
    return create_composition_from_manifest(
        manifest=manifest,
        organization=organization,
        creator=creator,
        token=token,
        log=log,
    )


def create_composition_auth_key(user: karakter_models.User, composition: models.Composition, ephemeral: bool = False, tags: list[str] = None) -> models.IonscaleAuthKey:
    
    layer = models.IonscaleLayer.objects.filter(
        organization=composition.organization,
    ).first()
    
    if not layer:
        raise Exception("No Ionscale layer found for organization")
    
    tags = ["tag:composition-"+str(composition.pk)] if tags is None else tags
    
    
    key = django_repo.create_auth_key(
        tailnet=layer.tailnet_name,
        ephemeral=ephemeral,
        pre_authorized=True,
        tags=tags
    )
    key = models.IonscaleAuthKey.objects.create(
        layer=layer,
        key=key,
        creator=user,
        ephemeral=ephemeral,
        tags=tags
    )
    return key

def render_server_fakts(composition: models.Composition, context: base_models.LinkingContext) -> CompositionClaimAnswer:
    
    
    self_claim = SelfClaim(
        deployment_name=context.deployment_name,
        alias=Alias(
            id="self",
            host=context.request.host,
            port=context.request.port,
            is_secure=context.request.is_secure,
            path="lok",
            challenge="ht"
        ),
    )
    
    auth_claim = CompositionAuthClaim(
        jwks_url=f"{context.request.base_url}/.well-known/jwks.json",
        ionscale_auth_key=composition.auth_key.key if composition.auth_key else None,
        ionscale_coord_url=settings.IONSCALE_COORD_URL,
    )

    instance_claims: Dict[str, CompositionInstanceClaim] = {}
    client_claims: Dict[str, CompositionClientClaim] = {}
    
    
    for instance in composition.instances.all():
        instance_claims[instance.token] = CompositionInstanceClaim(
            identifier=instance.token,
            private_key=instance.private_key,
        )
        
    for client in composition.clients.all():
        client_claims[client.token] = CompositionClientClaim(
            token=client.token,
        )
        
    claim = CompositionClaimAnswer(
        auth=auth_claim,
        self=self_claim,
        instances=instance_claims,
        clients=client_claims,
    )
    
    return claim
        
        
    
    

#TODO: Rename to render_fakts
def render_composition(client: models.Client, context: base_models.LinkingContext) -> dict:
    config_dict = {}

    self_claim = SelfClaim(
        deployment_name=context.deployment_name,
        alias=Alias(
            id="self",
            host=context.request.host,
            port=context.request.port,
            is_secure=context.request.is_secure,
            path="lok",
            challenge="ht"
        ),
        
    )

    auth_claim = AuthClaim(
        client_id=client.oauth2_client.client_id,
        client_secret=client.oauth2_client.client_secret,
        scopes=client.scopes.values_list("identifier", flat=True),
        client_token=client.token,
        report_url=f"{context.request.base_url}/f/report/",
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


def find_instance_for_requirement_and_composition(requirement: base_models.Requirement, user: models.AbstractUser, composition: models.Composition) -> models.ServiceInstance | None:
    instance = (
        models.ServiceInstance.objects.filter(
            release__service__identifier=requirement.service,
            composition=composition,
        )
        .filter(
            models.Q(allowed_users__isnull=True)
            | models.Q(allowed_users=user) & (models.Q(denied_users__isnull=True) | ~models.Q(denied_users=user)) & (models.Q(allowed_groups__isnull=True) | models.Q(allowed_groups__in=user.groups.all())) & (models.Q(denied_groups__isnull=True) | ~models.Q(denied_groups__in=user.groups.all()))
        )
        .first()
    )

    return instance


def hash_requirements(requirements: list[base_models.Requirement]) -> str:
    # Order the requirements by service and key and hash them
    return sha256(".".join(sorted([req.service + req.key for req in requirements])).encode()).hexdigest()


def auto_compose(client: models.Client, manifest: base_models.Manifest, user: models.AbstractUser, organization: models.Organization, device: models.ComputeNode | None = None) -> models.Client:
    requirements = manifest.requirements

    if not requirements:
        return client

    if hash_requirements(requirements) != client.requirements_hash or True:
        errors = []
        warnings = []

        for old_mapping in client.mappings.all():
            old_mapping.delete()

        for req in requirements:
            try:
                instance = find_instance_for_requirement_and_composition(req, user, composition=client.composition)

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
    
    
def create_serverlinking_context(request: HttpRequest, composition: models.Composition, claim: base_models.ServerClaimRequest) -> base_models.LinkingContext:
    host_string = request.get_host().split(":")
    if len(host_string) == 2:
        host = host_string[0]
        port = host_string[1]
    else:
        host = host_string[0]
        port = None

    base_url = request.build_absolute_uri("/") + settings.MY_SCRIPT_NAME

    return base_models.ServerLinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            base_url=base_url,
            is_secure=request.is_secure(),
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

            client = create_client(manifest=manifest, config=config, user=user, organization=org)

        device_code.client = client
        device_code.save()
        return device_code
    except models.DeviceCode.DoesNotExist:
        raise ValueError(f"Device code {literal_device_code} does not exist or is invalid.")

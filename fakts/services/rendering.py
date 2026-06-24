"""Rendering of fakts claims + requirement/instance resolution and composition.

These functions turn clients/compositions into the claim payloads handed back to
apps, resolve which service instance satisfies a requirement, and (re)compose a
client's service-instance mappings from its manifest.
"""

from typing import Dict

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest

from fakts import base_models, errors, models
from fakts.base_models import (
    Alias,
    AuthClaim,
    ClaimAnswer,
    CompositionAuthClaim,
    CompositionClaimAnswer,
    CompositionClientClaim,
    CompositionInstanceClaim,
    InstanceClaim,
    SelfClaim,
)
from fakts.services.tokens import hash_requirements


def render_server_fakts(composition: models.Composition, context: base_models.LinkingContext) -> CompositionClaimAnswer:
    self_claim = SelfClaim(
        deployment_name=context.deployment_name,
        alias=Alias(id="self", host=context.request.host, port=context.request.port, is_secure=context.request.is_secure, path="lok", challenge="ht"),
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


# TODO: Rename to render_fakts
def render_composition(client: models.Client, context: base_models.LinkingContext) -> dict:
    self_claim = SelfClaim(
        deployment_name=context.deployment_name,
        alias=Alias(id="self", host=context.request.host, port=context.request.port, is_secure=context.request.is_secure, path="lok", challenge="ht"),
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
        statuses=client.statuses,
    )

    return claim.model_dump()


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


@transaction.atomic
def auto_compose(client: models.Client, manifest: base_models.Manifest, user: models.AbstractUser, organization: models.Organization, device: models.Device | None = None, declined_requirements: list[str] | None = None) -> models.Client:
    requirements = manifest.requirements

    if not requirements:
        return client

    declined = set(declined_requirements or [])
    statuses: dict[str, str] = {}

    for old_mapping in client.mappings.all():
        old_mapping.delete()

    for req in requirements:
        if req.optional and req.key in declined:
            statuses[req.key] = "denied"
            continue

        try:
            instance = find_instance_for_requirement_and_composition(req, user, composition=client.composition)

            if instance is None:
                raise errors.InstanceNotFound(f"No instance for {req.service} in this composition.")

            models.ServiceInstanceMapping.objects.get_or_create(
                client=client,
                instance=instance,
                key=req.key,
            )
            statuses[req.key] = "granted"

        except Exception as e:
            if req.optional:
                statuses[req.key] = "unavailable"
            else:
                raise Exception(f"Unable to find instance for requirement {req.service}") from e

    client.requirements_hash = hash_requirements(requirements)
    client.statuses = statuses
    client.save()

    return client


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

"""Client lifecycle: creating development clients and redeeming tokens.

This module owns the creation of fakts ``Client`` (+ underlying ``OAuth2Client``)
records. It depends on :mod:`fakts.services.rendering` for ``auto_compose`` and on
:mod:`fakts.services.tokens`; it does *not* import device-code logic, which breaks
the historical ``logic`` <-> ``builders`` import cycle.
"""

from django.db import transaction
from django.utils import timezone

from authapp.models import generate_client_id, generate_client_secret
from fakts import base_models, enums, models
from fakts.base_models import Manifest
from fakts.services.rendering import auto_compose
from fakts.services.tokens import create_api_token
from karakter import models as karakter_models


class RedeemTokenExpired(Exception):
    """Raised when a redeem token has passed its expiry (and has been deleted)."""


@transaction.atomic
def create_development_client(
    release: models.Release,
    config: base_models.DevelopmentClientConfig,
    manifest: base_models.Manifest,
    node: models.ComputeNode | None = None,
    composition: models.Composition | None = None,
) -> models.Client:
    tenant = config.get_tenant()
    user = config.get_user()
    organization = config.get_organization()

    try:
        client = models.Client.objects.get(user=user, release=release, organization=organization, node=node, kind=enums.ClientKindVanilla.DEVELOPMENT.value)
        if client.token != config.token:
            client.token = config.token
        client.tenant = tenant
        client.node = node
        client.manifest = manifest.model_dump()
        client.membership = karakter_models.Membership.objects.get(user=user, organization=organization)
        client.composition = composition
        client.role = config.role.value if hasattr(config.role, "value") else config.role
        client.public_sources = [t.dict() for t in manifest.public_sources] if manifest.public_sources else []
        client.save()

        return client

    except models.Client.DoesNotExist:
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        oauth2_client = models.OAuth2Client.objects.create(
            client_id=client_id,
            client_secret=client_secret,
        )

        return models.Client.objects.create(
            release=release,
            user=user,
            tenant=user,
            membership=karakter_models.Membership.objects.get(user=user, organization=organization),
            node=node,
            token=config.token,
            kind=enums.ClientKindVanilla.DEVELOPMENT.value,
            role=config.role.value if hasattr(config.role, "value") else config.role,
            oauth2_client=oauth2_client,
            redirect_uris="",
            public=False,
            composition=composition,
            manifest=manifest.model_dump(),
            logo=release.logo,
            organization=organization,
            public_sources=[t.dict() for t in manifest.public_sources] if manifest.public_sources else [],
        )


@transaction.atomic
def create_client(
    manifest: base_models.Manifest,
    config: base_models.ClientConfig,
    user: models.AbstractUser,
    organization: models.Organization,
    composition: models.Composition | None = None,
    declined_requirements: list[str] | None = None,
) -> models.Client:
    from fakts.utils import download_logo

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None
    except Exception as e:
        raise ValueError(f"Could not download logo {e}")

    app, _ = models.App.objects.get_or_create(identifier=manifest.identifier)
    if logo:
        app.logo = logo
        app.save()

    release, _ = models.Release.objects.update_or_create(
        app=app,
        version=manifest.version,
        defaults={
            "logo": logo,
            "scopes": manifest.scopes,
            "requirements": manifest.dict()["requirements"],
        },
    )

    if manifest.node_id:
        node = models.ComputeNode.objects.get_or_create(organization=organization, node_id=manifest.node_id)[0]
    else:
        node = None

    if config.kind == enums.ClientKindVanilla.DEVELOPMENT.value:
        client = create_development_client(release, config, manifest, node=node, composition=composition)
    else:
        raise ValueError(f"Client kind {config.kind} not supported yet")

    client = auto_compose(client, manifest, user, organization, device=node, declined_requirements=declined_requirements)

    for scope in manifest.scopes or []:
        client.scopes.add(karakter_models.Scope.objects.get(identifier=scope, organization=organization))

    return client


@transaction.atomic
def validate_redeem_token(redeem_token: models.RedeemToken, manifest: Manifest, role: enums.ClientRoleVanilla = enums.ClientRoleVanilla.INTERFACE) -> models.RedeemToken:
    node_id = manifest.node_id
    composition = redeem_token.composition
    organization = redeem_token.composition.organization
    user = redeem_token.user

    if node_id:
        node, _ = models.ComputeNode.objects.get_or_create(organization=organization, node_id=node_id)
    else:
        node = None

    client = models.Client.objects.filter(
        release__app__identifier=manifest.identifier,
        release__version=manifest.version,
        kind="development",
        node=node,
        tenant=user,
        organization=organization,
        composition=composition,
        redirect_uris=None,
    ).first()

    if not client:
        token = create_api_token()

        config = base_models.DevelopmentClientConfig(
            kind=enums.ClientKindVanilla.DEVELOPMENT.value,
            role=role.value if hasattr(role, "value") else role,
            token=token,
            user=user.username,
            organization=organization.slug,
            tenant=user.username,
        )

        client = create_client(
            manifest=manifest,
            config=config,
            user=user,
            organization=organization,
            composition=composition,
        )

    redeem_token.client = client
    redeem_token.save()
    return redeem_token


def redeem_token(token: str, manifest: Manifest, role: enums.ClientRoleVanilla = enums.ClientRoleVanilla.INTERFACE) -> models.Client:
    """Redeem a token into a client.

    Raises ``RedeemToken.DoesNotExist`` for an unknown token and
    :class:`RedeemTokenExpired` for an expired one (which is deleted).
    """
    valid_token = models.RedeemToken.objects.get(token=token)

    if valid_token.expires_at and valid_token.expires_at < timezone.now():
        valid_token.delete()
        raise RedeemTokenExpired("Redeem token expired")

    if valid_token.client:
        return valid_token.client

    valid_token = validate_redeem_token(redeem_token=valid_token, manifest=manifest, role=role)
    return valid_token.client


@transaction.atomic
def report_client(claim: base_models.ReportRequest) -> models.Client:
    """Record a client's self-report (functional flag + per-requirement alias reports)."""
    client = models.Client.objects.get(token=claim.token)
    client.functional = claim.functional
    client.save()

    for req_key, alias_report in claim.alias_reports.items():
        alias = models.InstanceAlias.objects.get(id=alias_report.alias_id) if alias_report.alias_id else None

        models.UsedAlias.objects.update_or_create(
            client=client,
            key=req_key,
            defaults={
                "alias": alias,
                "valid": alias_report.valid,
                "reason": alias_report.reason,
                "used_at": timezone.now(),
            },
        )

    return client

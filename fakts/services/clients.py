"""Client lifecycle: creating development clients and redeeming tokens.

This module owns the creation of fakts ``Client`` (+ underlying ``OAuth2Client``)
records. It depends on :mod:`fakts.services.rendering` for ``auto_compose`` and on
:mod:`fakts.services.tokens`; it does *not* import device-code logic, which breaks
the historical ``logic`` <-> ``builders`` import cycle.
"""

import hashlib
import json

from django.db import transaction
from django.utils import timezone

from authapp.models import generate_client_id, generate_client_secret
from fakts import base_models, enums, models
from fakts.base_models import Manifest
from fakts.services.rendering import auto_compose
from fakts.services.tokens import create_api_token
from karakter import models as karakter_models
from karakter.hashers import hash_device_id


class RedeemTokenExpired(Exception):
    """Raised when a redeem token has passed its expiry (and has been deleted)."""


class RedeemTokenManifestChanged(Exception):
    """Raised when an already-redeemed token is re-redeemed with a different
    manifest while ``allow_reredeem`` is not set."""


def hash_manifest(manifest: Manifest) -> str:
    """Return a stable SHA-256 hash of a manifest for change detection."""
    return hashlib.sha256(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()


@transaction.atomic
def create_development_client(
    release: models.Release,
    config: base_models.DevelopmentClientConfig,
    manifest: base_models.Manifest,
    node: models.Device | None = None,
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
        client.public_sources = [t.model_dump() for t in manifest.public_sources] if manifest.public_sources else []
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
            public_sources=[t.model_dump() for t in manifest.public_sources] if manifest.public_sources else [],
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
            "requirements": manifest.model_dump()["requirements"],
        },
    )

    if manifest.node_id:
        node = models.Device.objects.get_or_create(organization=organization, node_id=hash_device_id(manifest.node_id, organization))[0]
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
        node, _ = models.Device.objects.get_or_create(organization=organization, node_id=hash_device_id(node_id, organization))
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
        redirect_uris="",
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
    with transaction.atomic():
        # Lock the token row so simultaneous redeems of the same token serialize
        # instead of racing to create duplicate clients.
        valid_token = models.RedeemToken.objects.select_for_update().get(token=token)

        if not (valid_token.expires_at and valid_token.expires_at < timezone.now()):
            incoming_hash = hash_manifest(manifest)

            if valid_token.client:
                if valid_token.manifest_hash is None:
                    # Pre-existing token from before manifest-hash tracking: record the
                    # hash and accept this redeem rather than treating it as a change.
                    valid_token.manifest_hash = incoming_hash
                    valid_token.save()
                    return valid_token.client
                if valid_token.manifest_hash == incoming_hash:
                    return valid_token.client
                if not valid_token.allow_reredeem:
                    raise RedeemTokenManifestChanged(
                        "This redeem token was already redeemed with a different manifest. "
                        "Re-redeeming with a changed manifest is not allowed unless allow_reredeem is set."
                    )
                # allow_reredeem is set and the manifest changed: re-validate to update the client.

            valid_token = validate_redeem_token(redeem_token=valid_token, manifest=manifest, role=role)
            valid_token.manifest_hash = incoming_hash
            valid_token.save()
            return valid_token.client

    # Reached only when the token is expired. Delete it *outside* the atomic block
    # above so the removal commits — deleting inside would be rolled back by the
    # raise (and the expired token would survive).
    models.RedeemToken.objects.filter(token=token).delete()
    raise RedeemTokenExpired("Redeem token expired")


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

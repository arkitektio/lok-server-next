"""Device-code flow: staging device codes and validating them into clients."""

import datetime
import logging

from django.db import transaction
from django.utils import timezone

from fakts import base_models, enums, models
from fakts.services.clients import create_client
from fakts.services.rendering import auto_compose
from fakts.services.tokens import create_api_token, create_device_code
from fakts.utils import download_logo
from karakter.hashers import hash_device_id

logger = logging.getLogger(__name__)


class LogoDownloadError(Exception):
    """Raised when a manifest logo could not be downloaded while staging a device code."""


def start_device_code(start_grant: base_models.DeviceCodeStartRequest) -> models.DeviceCode:
    """Stage a (client) device code from a start request, downloading the logo."""
    manifest = start_grant.manifest

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None
    except Exception as e:
        raise LogoDownloadError(str(e)) from e

    logger.info(f"Received start challenge for {manifest.identifier}:{manifest.version} {start_grant.request_public}")

    return models.DeviceCode.objects.create(
        code=create_device_code(),
        staging_manifest=manifest.model_dump(),
        expires_at=timezone.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
        staging_kind=start_grant.requested_client_kind.value,
        staging_role=start_grant.requested_client_role.value,
        staging_redirect_uris=start_grant.redirect_uris,
        staging_logo=logo,
        staging_public=start_grant.request_public,
    )


def start_service_device_code(start_grant: base_models.ServiceDeviceCodeStartRequest) -> models.ServiceDeviceCode:
    """Stage a service device code from a start request, downloading the logo."""
    manifest = start_grant.manifest

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None  # noqa: F841 (validates logo is reachable)
    except Exception as e:
        raise LogoDownloadError(str(e)) from e

    logger.info(f"Received start challenge for {manifest.identifier}:{manifest.version}")

    return models.ServiceDeviceCode.objects.create(
        code=create_device_code(),
        challenge_code=create_device_code(),
        staging_manifest=manifest.model_dump(),
        staging_aliases=[alias.model_dump() for alias in start_grant.staging_aliases],
        expires_at=timezone.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
    )


def start_composition_device_code(start_grant: base_models.CompositionStartRequest) -> models.CompositionDeviceCode:
    """Stage a composition device code from a start request, downloading the logo."""
    manifest = start_grant.composition

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None  # noqa: F841 (validates logo is reachable)
    except Exception as e:
        raise LogoDownloadError(str(e)) from e

    logger.info(f"Received start challenge for {manifest.identifier}")

    return models.CompositionDeviceCode.objects.create(
        code=create_device_code(),
        challenge_code=create_device_code(),
        manifest=manifest.model_dump(),
        expires_at=timezone.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
    )


@transaction.atomic
def validate_device_code(
    device_code: models.DeviceCode,
    user: models.AbstractUser,
    organization: models.Organization,
    composition: models.Composition,
    declined_requirements: list[str] | None = None,
) -> models.DeviceCode:
    manifest = device_code.manifest_as_model

    node_id = manifest.node_id
    if node_id:
        node, _ = models.Device.objects.get_or_create(organization=organization, node_id=hash_device_id(node_id, organization))
    else:
        node = None

    redirect_uris = (" ".join(device_code.staging_redirect_uris),)

    client = models.Client.objects.filter(
        release__app__identifier=device_code.staging_manifest["identifier"],
        release__version=device_code.staging_manifest["version"],
        kind=device_code.staging_kind,
        node=node,
        tenant=user,
        organization=organization,
        composition=composition,
        redirect_uris=redirect_uris,
    ).first()

    if not client:
        token = create_api_token()

        config = None

        if device_code.staging_kind == enums.ClientKindVanilla.DEVELOPMENT.value:
            config = base_models.DevelopmentClientConfig(
                kind=enums.ClientKindVanilla.DEVELOPMENT.value,
                role=device_code.staging_role,
                token=token,
                user=user.username,
                organization=organization.slug,
                tenant=user.username,
            )

        else:
            raise Exception("Unknown client kind or no longer supported")

        client = create_client(
            manifest=manifest,
            config=config,
            user=user,
            organization=organization,
            composition=composition,
            declined_requirements=declined_requirements,
        )

    else:
        auto_compose(client, manifest, user, organization, declined_requirements=declined_requirements)

    device_code.client = client
    device_code.save()
    return device_code

"""Composition lifecycle: building compositions from manifests/partners.

Includes the partner pre-authorization webhook and the auto-configuration of
kommunity partners for an organization.
"""

import logging
from uuid import NAMESPACE_DNS, uuid5

import requests
from django.db import transaction

from fakts import models
from fakts.base_models import CompositionManifest
from fakts.services.tokens import create_api_token  # noqa: F401  (kept for shim parity)
from ionscale.repo import django_repo
from karakter import models as karakter_models

logger = logging.getLogger(__name__)


class PartnerPreAuthorizationError(Exception):
    """Raised when a partner pre-authorization hook rejects a composition."""


def run_partner_pre_authorize_hook(
    partner: models.KommunityPartner,
    organization: karakter_models.Organization,
    composition: models.Composition,
    composition_config: dict | None,
    license_signature: str | None = None,
) -> None:
    """Call an optional partner pre-authorization hook and require an explicit OK response."""
    if not partner.pre_authorize_hook:
        return

    headers = {
        "Content-Type": "application/json",
    }
    if partner.pre_authorize_token:
        headers["Authorization"] = f"Bearer {partner.pre_authorize_token}"

    payload = {
        "partner": {
            "id": str(partner.pk),
            "identifier": partner.identifier,
            "name": partner.name,
        },
        "organization": {
            "id": str(organization.pk),
            "slug": organization.slug,
            "name": organization.name,
        },
        "composition": {
            "id": str(composition.pk),
            "identifier": composition.identifier,
            "name": composition.name,
            "token": composition.token,
        },
        "composition_config": composition_config,
    }
    if license_signature:
        payload["license_signature"] = license_signature

    try:
        response = requests.post(
            partner.pre_authorize_hook,
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PartnerPreAuthorizationError(
            f"Partner approval failed for '{partner.name}'. The approval hook could not be reached."
        ) from exc

    approval_message = None
    try:
        response_data = response.json()
    except ValueError:
        response_text = response.text.strip().lower()
        if response_text == "ok":
            return
        approval_message = response.text.strip() or None
    else:
        if isinstance(response_data, dict):
            if response_data.get("ok") is True:
                return

            for key in ("status", "answer", "result"):
                value = response_data.get(key)
                if isinstance(value, str) and value.strip().lower() == "ok":
                    return

            approval_message = response_data.get("message") or response_data.get("error") or response_data.get("detail")
        elif isinstance(response_data, str) and response_data.strip().lower() == "ok":
            return
        elif isinstance(response_data, str):
            approval_message = response_data.strip() or None

    raise PartnerPreAuthorizationError(
        approval_message or f"Partner approval failed for '{partner.name}'. The approval hook did not return ok."
    )


@transaction.atomic
def create_composition_from_manifest(
    manifest: CompositionManifest,
    organization: karakter_models.Organization,
) -> models.Composition:
    """Create or update a composition (and its instances/roles/scopes/aliases) from a manifest."""
    token = str(uuid5(NAMESPACE_DNS, f"{manifest.identifier}:{organization.slug}"))

    composition, created = models.Composition.objects.update_or_create(
        identifier=manifest.identifier,
        organization=organization,
        defaults={
            "token": token,
            "name": manifest.identifier or "Unnamed Composition",
            "description": manifest.description or "Auto-configured composition",
            "organization": organization,
            "creator": organization.owner,
        },
    )

    logger.info(f"{'Created' if created else 'Updated'} composition '{composition.name}' for org '{organization.slug}'")

    for instance_request in manifest.instances:
        service_manifest = instance_request.manifest

        service, _ = models.Service.objects.get_or_create(identifier=service_manifest.identifier, defaults={"name": service_manifest.identifier})

        release, _ = models.ServiceRelease.objects.get_or_create(service=service, version=service_manifest.version)

        instance, inst_created = models.ServiceInstance.objects.update_or_create(
            token=instance_request.identifier,
            composition=composition,
            defaults={
                "steward": organization.owner,
                "release": release,
                "organization": organization,
                "template": "{}",
                "instance_id": instance_request.identifier,
            },
        )

        logger.info(f"  {'Created' if inst_created else 'Updated'} instance: {instance.token}")

        if service_manifest.roles:
            for role_config in service_manifest.roles:
                role, role_created = karakter_models.Role.objects.get_or_create(organization=organization, identifier=role_config.key, defaults={"description": role_config.description, "creating_instance": instance})
                role.used_by.add(instance)
                logger.info(f"    {'Created' if role_created else 'Updated'} role: {role.identifier}")

        if service_manifest.scopes:
            for scope_config in service_manifest.scopes:
                scope, scope_created = karakter_models.Scope.objects.get_or_create(organization=organization, identifier=scope_config.key, defaults={"description": scope_config.description, "creating_instance": instance})
                scope.used_by.add(instance)
                logger.info(f"    {'Created' if scope_created else 'Updated'} scope: {scope.identifier}")

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
                },
            )
            logger.info(f"    {'Created' if alias_created else 'Updated'} alias: {alias_obj.name}")

    return composition


def create_composition_from_partner(
    partner: models.KommunityPartner,
    organization: karakter_models.Organization,
    license_signature: str | None = None,
) -> models.Composition | None:
    """Create a composition from a partner's preconfigured composition, honouring its pre-auth hook."""
    manifest = partner.preconfigured_composition_as_model
    if not manifest:
        raise ValueError(f"Partner '{partner.identifier}' has no preconfigured composition")

    logger.info(f"Creating composition from partner '{partner.identifier}' for org '{organization.slug}' ")

    composition = create_composition_from_manifest(
        manifest=manifest,
        organization=organization,
    )

    try:
        run_partner_pre_authorize_hook(
            partner=partner,
            organization=organization,
            composition=composition,
            composition_config=partner.preconfigured_composition,
            license_signature=license_signature,
        )
    except PartnerPreAuthorizationError:
        logger.exception(
            "Partner pre-authorization rejected composition '%s' for organization '%s'; deleting composition.",
            composition.identifier,
            organization.slug,
        )
        composition.delete()
        raise

    return composition


def auto_configure_kommunity_partners(
    organization: karakter_models.Organization,
) -> list[str]:
    """Apply every auto-configure kommunity partner that matches the organization's owner."""
    applied_partners = []

    auto_configure_partners = models.KommunityPartner.objects.filter(auto_configure=True)
    user = organization.owner

    for partner in auto_configure_partners:
        if not partner.applies_to_user(organization.owner):
            logger.info(f"Partner '{partner.identifier}' does not apply to user '{user}'")
            continue

        if not partner.preconfigured_composition:
            logger.warning(f"Partner '{partner.identifier}' has no preconfigured composition")
            continue

        logger.info(f"Applying partner '{partner.identifier}' to organization '{organization.slug}'")

        try:
            create_composition_from_partner(
                partner=partner,
                organization=organization,
            )
        except PartnerPreAuthorizationError:
            logger.warning(
                "Skipping auto-configured partner '%s' for organization '%s' because the pre-authorization hook rejected it.",
                partner.identifier,
                organization.slug,
            )
            continue

        applied_partners.append(partner.identifier)

    return applied_partners


def create_composition_auth_key(user: karakter_models.User, composition: models.Composition, ephemeral: bool = False, tags: list[str] = None) -> models.IonscaleAuthKey:
    layer = models.IonscaleLayer.objects.filter(
        organization=composition.organization,
    ).first()

    if not layer:
        raise Exception("No Ionscale layer found for organization")

    tags = ["tag:composition-" + str(composition.pk)] if tags is None else tags

    key = django_repo.create_auth_key(tailnet=layer.tailnet_name, ephemeral=ephemeral, pre_authorized=True, tags=tags)
    key = models.IonscaleAuthKey.objects.create(layer=layer, key=key, creator=user, ephemeral=ephemeral, tags=tags)
    return key

import logging

from django.conf import settings

from fakts.models import IonscaleLayer
from karakter.models import Membership
from . import base_models
from .repo import get_ionscale_repo

logger = logging.getLogger(__name__)

# Kept as a literal (matches api.management.enums.LayerKind.IONSCALE) so this
# lower-level module doesn't import the management app. Layer.kind is a free
# CharField, so the raw value is all that's stored.
_IONSCALE_KIND = "ionscale"


def ionscale_configured() -> bool:
    """Whether an ionscale backend is available (real CLI settings or a test/fake
    repository). When False, mesh provisioning is skipped rather than crashing."""
    return bool(
        getattr(settings, "IONSCALE_REPOSITORY", None)
        or getattr(settings, "IONSCALE_SERVER_URL", None)
    )


def get_org_mesh(organization) -> IonscaleLayer | None:
    """Return the organization's existing ionscale mesh, or None. Read-only — does
    not provision (that only happens via explicit opt-in, `ensure_org_mesh`)."""
    return IonscaleLayer.objects.filter(organization=organization).first()


def ensure_org_mesh(organization) -> IonscaleLayer | None:
    """Return the organization's single ionscale mesh, provisioning it on first
    opt-in.

    Singleton: if the org already has an ``IonscaleLayer`` it is returned as-is
    (this also removes the nondeterministic ``.first()`` ambiguity in callers).
    Returns ``None`` (and logs) when ionscale isn't configured or provisioning
    fails, so callers can degrade gracefully instead of breaking org flows.
    """
    existing = get_org_mesh(organization)
    if existing:
        return existing

    if not ionscale_configured():
        logger.warning(
            "Ionscale is not configured; skipping mesh provisioning for organization %s",
            organization,
        )
        return None

    # There is exactly one network per organization, so the tailnet is named after
    # the organization itself (its slug) rather than a "<slug>-default" variant.
    tailnet_name = str(organization.slug or organization.pk)
    try:
        get_ionscale_repo().create_tailnet(base_models.TailnetCreate(name=tailnet_name))
        layer = IonscaleLayer.objects.create(
            organization=organization,
            name=organization.name or tailnet_name,
            kind=_IONSCALE_KIND,
            identifier=tailnet_name,
            tailnet_name=tailnet_name,
        )
        sync(layer)
        apply_dns_config(layer)
        return layer
    except Exception:
        logger.exception(
            "Failed to provision ionscale mesh for organization %s", organization
        )
        return None


def sync(layer: IonscaleLayer) -> IonscaleLayer:
    # Create iam policy for all organization members
    members = Membership.objects.filter(organization=layer.organization).select_related("user")

    # Build policy
    policy = {
        "subs": [str(m.user.pk) for m in members]
    }

    get_ionscale_repo().update_policy(layer.tailnet_name, policy)

    return layer


def apply_dns_config(layer: IonscaleLayer, raise_on_error: bool = False) -> IonscaleLayer:
    """Push the mesh's desired DNS state (MagicDNS + HTTPS certs) to ionscale.

    Kept separate from `sync` (which runs on every membership change) so a DNS/ACME
    failure can't break member management and DNS isn't needlessly re-pushed. lok is
    the source of truth: `set-dns` replaces the whole config, so we always send the
    full desired state built from the model.

    ``raise_on_error`` controls failure handling: provisioning (`ensure_org_mesh`)
    leaves it False so a DNS hiccup doesn't fail org creation, but an *explicit* user
    toggle passes True so the failure surfaces to the caller (and the UI) instead of
    silently reporting success while ionscale never got the change.
    """
    if not ionscale_configured():
        logger.warning(
            "Ionscale is not configured; skipping DNS config for mesh %s", layer
        )
        return layer

    config = base_models.DNSConfig(
        magic_dns=layer.magic_dns_enabled,
        https_certs=layer.https_enabled,
    )
    try:
        get_ionscale_repo().set_dns_config(layer.tailnet_name, config)
    except Exception:
        logger.exception("Failed to apply DNS config for mesh %s", layer)
        if raise_on_error:
            raise

    return layer


def sync_organization_layers(organization) -> None:
    layers = IonscaleLayer.objects.filter(organization=organization)
    for layer in layers:
        sync(layer)
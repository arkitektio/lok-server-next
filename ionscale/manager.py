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

    tailnet_name = f"{organization.slug or organization.pk}-default"
    try:
        get_ionscale_repo().create_tailnet(base_models.TailnetCreate(name=tailnet_name))
        layer = IonscaleLayer.objects.create(
            organization=organization,
            name="Default",
            kind=_IONSCALE_KIND,
            identifier=tailnet_name,
            tailnet_name=tailnet_name,
        )
        sync(layer)
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


def sync_organization_layers(organization) -> None:
    layers = IonscaleLayer.objects.filter(organization=organization)
    for layer in layers:
        sync(layer)
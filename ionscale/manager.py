from fakts.models import IonscaleLayer
from karakter.models import Membership
from .repo import django_repo


def sync(layer: IonscaleLayer) -> IonscaleLayer:
    # Create iam policy for all organization members
    members = Membership.objects.filter(organization=layer.organization).select_related("user")

    # Build policy
    policy = {
        "subs": [str(m.user.pk) for m in members]
    }

    django_repo.update_policy(layer.tailnet_name, policy)

    return layer


def sync_organization_layers(organization) -> None:
    layers = IonscaleLayer.objects.filter(organization=organization)
    for layer in layers:
        sync(layer)
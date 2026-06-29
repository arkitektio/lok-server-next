from types import SimpleNamespace
from typing import cast

import pytest

from api.management.mutations.ionscale import CreateIonscaleLayerInput, create_ionscale_layer
from fakts import models as fakts_models
from karakter.models import Membership, Organization, User


@pytest.mark.django_db
def test_membership_changes_resync_ionscale_layers(ionscale_repo):
    existing_user = User.objects.create(username="existing-user")
    # owner is required; the org post_save signal makes the owner an admin member,
    # so we don't create the membership for ``existing_user`` explicitly.
    organization = Organization.objects.create(slug="ionscale-sync-org", owner=existing_user)
    fakts_models.IonscaleLayer.objects.create(
        organization=organization,
        name="Default",
        kind="ionscale",
        identifier="ionscale-sync-org-default",
        tailnet_name="ionscale-sync-org-default",
    )

    new_user = User.objects.create(username="new-user")
    membership = Membership.objects.create(user=new_user, organization=organization)

    assert len(ionscale_repo.updated_policies) == 1
    tailnet, policy = ionscale_repo.updated_policies[-1]
    assert tailnet == "ionscale-sync-org-default"
    assert set(policy["subs"]) == {str(existing_user.pk), str(new_user.pk)}

    ionscale_repo.updated_policies.clear()

    membership.delete()

    assert len(ionscale_repo.updated_policies) == 1
    tailnet, policy = ionscale_repo.updated_policies[-1]
    assert tailnet == "ionscale-sync-org-default"
    assert set(policy["subs"]) == {str(existing_user.pk)}


@pytest.mark.django_db
def test_create_ionscale_layer_syncs_existing_members(ionscale_repo):
    first_user = User.objects.create(username="first-user")
    second_user = User.objects.create(username="second-user")
    # owner is required; the org post_save signal makes ``first_user`` an admin
    # member, so only ``second_user``'s membership is created explicitly.
    organization = Organization.objects.create(slug="ionscale-create-org", owner=first_user)
    Membership.objects.create(user=second_user, organization=organization)

    layer = create_ionscale_layer(
        info=None,
        input=cast(
            CreateIonscaleLayerInput,
            SimpleNamespace(organization_id=organization.pk, name="Default"),
        ),
    )

    assert len(ionscale_repo.created_tailnets) == 1
    assert ionscale_repo.created_tailnets[0].name == "ionscale-create-org-default"
    assert layer.tailnet_name == "ionscale-create-org-default"
    assert ionscale_repo.updated_policies == [
        ("ionscale-create-org-default", {"subs": [str(first_user.pk), str(second_user.pk)]}),
    ]

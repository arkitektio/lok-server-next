from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

import pytest

from api.management.mutations.ionscale import CreateIonscaleLayerInput, create_ionscale_layer
from fakts import models as fakts_models
from karakter.models import Membership, Organization, User


@pytest.mark.django_db
def test_membership_changes_resync_ionscale_layers():
    organization = Organization.objects.create(slug="ionscale-sync-org")
    existing_user = User.objects.create(username="existing-user")
    Membership.objects.create(user=existing_user, organization=organization)
    fakts_models.IonscaleLayer.objects.create(
        organization=organization,
        name="Default",
        kind="ionscale",
        identifier="ionscale-sync-org-default",
        tailnet_name="ionscale-sync-org-default",
    )

    with patch("ionscale.manager.django_repo.update_policy") as update_policy:
        new_user = User.objects.create(username="new-user")
        membership = Membership.objects.create(user=new_user, organization=organization)

        assert update_policy.call_count == 1
        assert update_policy.call_args.args[0] == "ionscale-sync-org-default"
        assert set(update_policy.call_args.args[1]["subs"]) == {
            str(existing_user.pk),
            str(new_user.pk),
        }

        update_policy.reset_mock()

        membership.delete()

        assert update_policy.call_count == 1
        assert update_policy.call_args.args[0] == "ionscale-sync-org-default"
        assert set(update_policy.call_args.args[1]["subs"]) == {str(existing_user.pk)}


@pytest.mark.django_db
def test_create_ionscale_layer_syncs_existing_members():
    organization = Organization.objects.create(slug="ionscale-create-org")
    first_user = User.objects.create(username="first-user")
    second_user = User.objects.create(username="second-user")
    Membership.objects.create(user=first_user, organization=organization)
    Membership.objects.create(user=second_user, organization=organization)

    with patch("api.management.mutations.ionscale.django_repo.create_tailnet") as create_tailnet:
        with patch("ionscale.manager.django_repo.update_policy") as update_policy:
            layer = create_ionscale_layer(
                info=None,
                input=cast(
                    CreateIonscaleLayerInput,
                    SimpleNamespace(organization_id=organization.pk, name="Default"),
                ),
            )

    create_tailnet.assert_called_once()
    assert layer.tailnet_name == "ionscale-create-org-default"
    update_policy.assert_called_once_with(
        "ionscale-create-org-default",
        {"subs": [str(first_user.pk), str(second_user.pk)]},
    )
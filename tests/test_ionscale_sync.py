from types import SimpleNamespace
from typing import cast
from unittest import mock

import pytest

from api.management.mutations.ionscale import CreateIonscaleLayerInput, create_ionscale_layer
from fakts import models as fakts_models
from ionscale.base_models import DNSConfig
from ionscale.repo import IonscaleRepository
from karakter.models import Membership, Organization, User


def _info_for(user):
    """Minimal Info stand-in carrying a principal, matching ``tests/test_mesh``."""
    return SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=user)))


def _repo() -> IonscaleRepository:
    # Bypass the binary lookup in __init__ so the arg-building logic can be tested
    # without an ionscale binary present.
    with mock.patch("ionscale.repo.shutil.which", return_value="/usr/bin/ionscale"):
        return IonscaleRepository(server_url="http://ionscale", admin_key="k")


def test_set_dns_config_enable_both():
    """MagicDNS + HTTPS on → both flags present."""
    repo = _repo()
    with mock.patch.object(repo, "_run_command", return_value="ok") as run:
        repo.set_dns_config("tn", DNSConfig(magic_dns=True, https_certs=True))
    assert run.call_args.args[0] == [
        "tailnets", "set-dns", "--tailnet", "tn", "--magic-dns", "--https-certs",
    ]


def test_set_dns_config_disable_by_omission():
    """Disabling = omitting the flag. Relies on set-dns replacing the whole config."""
    repo = _repo()
    with mock.patch.object(repo, "_run_command", return_value="ok") as run:
        repo.set_dns_config("tn", DNSConfig(magic_dns=False, https_certs=False))
    assert run.call_args.args[0] == ["tailnets", "set-dns", "--tailnet", "tn"]


def test_set_dns_config_magic_on_https_off():
    """MagicDNS on, HTTPS off → only --magic-dns."""
    repo = _repo()
    with mock.patch.object(repo, "_run_command", return_value="ok") as run:
        repo.set_dns_config("tn", DNSConfig(magic_dns=True, https_certs=False))
    assert run.call_args.args[0] == [
        "tailnets", "set-dns", "--tailnet", "tn", "--magic-dns",
    ]


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
        info=_info_for(first_user),
        input=cast(
            CreateIonscaleLayerInput,
            SimpleNamespace(organization_id=organization.pk, name="Default"),
        ),
    )

    assert len(ionscale_repo.created_tailnets) == 1
    assert ionscale_repo.created_tailnets[0].name == "ionscale-create-org"
    assert layer.tailnet_name == "ionscale-create-org"
    assert ionscale_repo.updated_policies == [
        ("ionscale-create-org", {"subs": [str(first_user.pk), str(second_user.pk)]}),
    ]

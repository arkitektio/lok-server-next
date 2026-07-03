"""Opt-in ionscale mesh: singleton provisioning + graceful degradation.

The mesh is a per-organization singleton, provisioned only on explicit opt-in
(`ensure_org_mesh`). Compositions use the org's existing mesh read-only and give
an actionable message when there is none, instead of a bare failure.
"""

from types import SimpleNamespace

import pytest
from django.test import override_settings

from fakts import models as fakts_models
from fakts import enums as fakts_enums
from fakts.services.compositions import create_composition_auth_key
from ionscale.manager import ensure_org_mesh, get_org_mesh
from tests import factories


def _linking(host="go.example", port=443, is_secure=True):
    return SimpleNamespace(request=SimpleNamespace(host=host, port=port, is_secure=is_secure))


def test_alias_render_is_layer_independent():
    """A rendered client alias is self-contained — `to_url` never reads the layer,
    so the client contract does not depend on the (deprecated) layer concept."""
    # ABSOLUTE alias with no layer → uses its own host/port/ssl.
    absolute = fakts_models.InstanceAlias(
        kind=fakts_enums.AliasKindChoices.ABSOLUTE.value,
        host="svc.example", port=8080, ssl=True, path="p", challenge="ht", public=True, layer=None,
    )
    a = absolute.to_url(_linking())
    assert a.host == "svc.example" and a.port == 8080 and a.ssl is True

    # RELATIVE alias with no layer → resolves against the linking request host.
    relative = fakts_models.InstanceAlias(
        kind=fakts_enums.AliasKindChoices.RELATIVE.value,
        host=None, port=None, ssl=True, path="p", challenge="ht", public=False, layer=None,
    )
    r = relative.to_url(_linking(host="coord.example", port=443, is_secure=True))
    assert r.host == "coord.example" and r.port == 443


@pytest.mark.django_db
def test_ensure_org_mesh_is_idempotent_singleton(ionscale_repo):
    org = factories.make_organization()

    mesh1 = ensure_org_mesh(org)
    assert mesh1 is not None
    assert fakts_models.IonscaleLayer.objects.filter(organization=org).count() == 1
    assert len(ionscale_repo.created_tailnets) == 1

    # Second call returns the same mesh; no second tailnet.
    mesh2 = ensure_org_mesh(org)
    assert mesh2.pk == mesh1.pk
    assert fakts_models.IonscaleLayer.objects.filter(organization=org).count() == 1
    assert len(ionscale_repo.created_tailnets) == 1


@pytest.mark.django_db
@override_settings(IONSCALE_REPOSITORY=None, IONSCALE_SERVER_URL=None)
def test_ensure_org_mesh_is_noop_when_ionscale_unconfigured():
    org = factories.make_organization()
    # Degrades gracefully — no mesh, no exception into the org flow.
    assert ensure_org_mesh(org) is None
    assert get_org_mesh(org) is None
    assert fakts_models.IonscaleLayer.objects.filter(organization=org).count() == 0


@pytest.mark.django_db
def test_create_organization_enables_mesh_by_default(ionscale_repo):
    """Creating an organization auto-provisions its mesh (enabled by default)."""
    from types import SimpleNamespace
    from karakter.graphql.mutations.organization import create_organization, CreateOrganizationInput

    user = factories.make_user()
    info = SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=user)))
    org = create_organization(info, CreateOrganizationInput(name="Meshy Org", description="d"))

    assert fakts_models.IonscaleLayer.objects.filter(organization=org).count() == 1
    assert len(ionscale_repo.created_tailnets) == 1


@pytest.mark.django_db
def test_composition_auth_key_needs_opted_in_mesh(ionscale_repo):
    composition = factories.make_composition()
    org = composition.organization

    # No mesh opted in yet -> actionable message, and no tailnet auto-created.
    with pytest.raises(Exception, match="no mesh"):
        create_composition_auth_key(org.owner, composition)
    assert len(ionscale_repo.created_tailnets) == 0

    # Opt in, then issuing a key works against the singleton mesh.
    ensure_org_mesh(org)
    key = create_composition_auth_key(org.owner, composition)
    assert key.pk is not None
    assert len(ionscale_repo.created_auth_keys) == 1
    assert ionscale_repo.created_auth_keys[-1]["tailnet"] == get_org_mesh(org).tailnet_name

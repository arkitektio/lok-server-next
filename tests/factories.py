"""Lightweight object factories for the lok test suite.

Implemented as plain helper functions (no factory-boy dependency, which cannot
be installed in the build environment). Each ``make_*`` helper fills in sensible,
internally-consistent defaults and accepts keyword overrides, so tests don't have
to hand-wire every FK.

Relationships are kept consistent by default (e.g. a ``Client``'s
``user``/``organization`` derive from its membership).
"""

import itertools
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone

from karakter.models import Organization, User, Membership
from authapp.models import OAuth2Client, generate_client_id, generate_client_secret
from fakts import models as fmodels
from fakts.enums import ClientKindChoices, ClientRoleChoices

_seq = itertools.count(1)


def _n() -> int:
    return next(_seq)


def make_user(**kw) -> User:
    kw.setdefault("username", f"user{_n()}")
    kw.setdefault("email", f"{kw['username']}@example.com")
    return User.objects.create(**kw)


def make_organization(owner: User | None = None, **kw) -> Organization:
    if owner is None:
        owner = make_user()
    kw.setdefault("slug", f"org{_n()}")
    kw.setdefault("name", kw["slug"].title())
    return Organization.objects.create(owner=owner, **kw)


def make_membership(user: User | None = None, organization: Organization | None = None, **kw) -> Membership:
    if user is None:
        user = make_user()
    if organization is None:
        organization = make_organization()
    membership, _ = Membership.objects.get_or_create(user=user, organization=organization, defaults=kw)
    return membership


def make_oauth2_client(membership: Membership | None = None, **kw) -> OAuth2Client:
    if membership is None:
        membership = make_membership()
    kw.setdefault("client_id", generate_client_id())
    kw.setdefault("client_secret", generate_client_secret())
    return OAuth2Client.objects.create(membership=membership, **kw)


def make_app(**kw) -> fmodels.App:
    n = _n()
    kw.setdefault("name", f"App {n}")
    kw.setdefault("identifier", f"com.example.app{n}")
    return fmodels.App.objects.create(**kw)


def make_release(app: fmodels.App | None = None, **kw) -> fmodels.Release:
    if app is None:
        app = make_app()
    kw.setdefault("version", "1.0.0")
    kw.setdefault("name", f"{app.name} {kw['version']}")
    return fmodels.Release.objects.create(app=app, **kw)


def make_client(membership: Membership | None = None, release: fmodels.Release | None = None, **kw) -> fmodels.Client:
    if membership is None:
        membership = make_membership()
    if release is None:
        release = make_release()
    kw.setdefault("user", membership.user)
    kw.setdefault("tenant", membership.user)
    kw.setdefault("organization", membership.organization)
    kw.setdefault("oauth2_client", make_oauth2_client(membership=membership))
    kw.setdefault("kind", ClientKindChoices.DEVELOPMENT.value)
    kw.setdefault("role", ClientRoleChoices.INTERFACE.value)
    # the model default is a UUID object; production tokens are strings, so make
    # the in-memory instance hold a string too (avoids UUID-not-JSON-serializable).
    kw.setdefault("token", str(uuid4()))
    return fmodels.Client.objects.create(release=release, membership=membership, **kw)


def make_composition(organization: Organization | None = None, **kw) -> fmodels.Composition:
    if organization is None:
        organization = make_organization()
    n = _n()
    kw.setdefault("name", f"composition-{n}")
    kw.setdefault("identifier", f"comp{n}")
    kw.setdefault("creator", organization.owner)
    return fmodels.Composition.objects.create(organization=organization, **kw)


def make_service(**kw) -> fmodels.Service:
    n = _n()
    kw.setdefault("name", f"Service {n}")
    kw.setdefault("identifier", f"com.example.service{n}")
    return fmodels.Service.objects.create(**kw)


def make_service_release(service: fmodels.Service | None = None, **kw) -> fmodels.ServiceRelease:
    if service is None:
        service = make_service()
    kw.setdefault("version", "1.0.0")
    return fmodels.ServiceRelease.objects.create(service=service, **kw)


def make_service_instance(composition: fmodels.Composition | None = None, release: fmodels.ServiceRelease | None = None, **kw) -> fmodels.ServiceInstance:
    if composition is None:
        composition = make_composition()
    if release is None:
        release = make_service_release()
    kw.setdefault("organization", composition.organization)
    kw.setdefault("steward", composition.creator)
    kw.setdefault("template", "{}")
    kw.setdefault("token", f"instance-token-{_n()}")
    return fmodels.ServiceInstance.objects.create(composition=composition, release=release, **kw)


def make_device_code(**kw) -> fmodels.DeviceCode:
    kw.setdefault("code", f"device-code-{_n()}")
    kw.setdefault(
        "staging_manifest",
        {"identifier": "com.example.app", "version": "1.0.0", "scopes": [], "requirements": []},
    )
    kw.setdefault("staging_kind", ClientKindChoices.DEVELOPMENT.value)
    kw.setdefault("staging_role", ClientRoleChoices.INTERFACE.value)
    kw.setdefault("expires_at", timezone.now() + timedelta(seconds=300))
    return fmodels.DeviceCode.objects.create(**kw)


def make_redeem_token(composition: fmodels.Composition | None = None, **kw) -> fmodels.RedeemToken:
    if composition is None:
        composition = make_composition()
    kw.setdefault("organization", composition.organization)
    kw.setdefault("user", composition.creator)
    kw.setdefault("token", str(uuid4()))
    return fmodels.RedeemToken.objects.create(composition=composition, **kw)

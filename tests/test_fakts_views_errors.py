"""Unhappy-path HTTP tests for the Fakts protocol endpoints (fakts/views.py).

Complements ``test_fakts_flows.py`` (which covers the happy paths of the
canonical grant) by exercising the error branches: malformed bodies,
expired/denied device codes at the token endpoint, logo-download failures, and
the report endpoint's Bearer authentication.

Note: malformed requests return **HTTP 200** with a ``{"status": "error"}`` body
(``_parse`` builds a default-status ``JsonResponse``), so assertions are on the
JSON body, not the status code — except the explicit 405 (wrong-method) and the
report endpoint's 401 cases.
"""

import json
import time
from datetime import timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from joserfc import jwt
from joserfc.jwk import RSAKey

from fakts import models
from fakts.services import device_codes
from tests import factories

DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"


def _post(client, name, payload, **kw):
    return client.post(reverse(name), data=json.dumps(payload), content_type="application/json", **kw)


def _manifest(version="1.0.0", **extra):
    return {"identifier": "com.example.errors", "version": version, "scopes": [], "requirements": [], **extra}


def _bearer_headers(fakts_client, exp_offset=60, **claim_overrides):
    key = RSAKey.import_key(settings.PRIVATE_KEY)
    claims = {
        "client_id": fakts_client.client_id,
        "exp": int(time.time()) + exp_offset,
        "iss": settings.OIDC_ISSUER,
        "aud": ["lok"],
    }
    claims.update(claim_overrides)
    token = jwt.encode({"alg": "RS256"}, claims, key)
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Malformed bodies / wrong method
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_start_malformed_json_returns_error(client):
    # Body is not valid JSON -> json.loads raises -> malformed envelope (key "error").
    resp = client.post(reverse("app_authorization"), data="{not json", content_type="application/json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert body["error"].startswith("Malformed request")


@pytest.mark.django_db
def test_get_on_post_only_view_returns_405(client):
    resp = client.get(reverse("app_authorization"))
    assert resp.status_code == 405


# --------------------------------------------------------------------------- #
# Device codes: expired codes at the token endpoint + purge
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_expired_code_yields_expired_token_at_token_endpoint(client):
    device_code = factories.make_device_code(expires_at=timezone.now() - timedelta(seconds=1))

    resp = client.post(
        reverse("token"),
        data={
            "grant_type": DEVICE_CODE_GRANT,
            "device_code": device_code.secret,
            "client_id": device_code.client.client_id,
        },
        secure=True,
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "expired_token"


@pytest.mark.django_db
def test_purge_reaps_expired_unapproved_codes_and_their_clients(client):

    device_code = factories.make_device_code(expires_at=timezone.now() - timedelta(seconds=1))
    orphan_client_id = device_code.client.client_id

    purged = device_codes.purge_expired_device_codes()

    assert purged == 1
    assert not models.DeviceCode.objects.filter(pk=device_code.pk).exists()
    assert not models.Client.objects.filter(client_id=orphan_client_id).exists()


# --------------------------------------------------------------------------- #
# Hub authorization (RFC 8628 shaped, /o/hub-authorization/)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_hub_authorization_registers_a_public_client(client):
    body = _post(
        client,
        "hub_authorization",
        {"hub": {"identifier": "com.example.comp"}},
    ).json()
    assert body["status"] == "granted"
    assert body["device_code"] != body["user_code"]
    assert body["token_endpoint"].endswith("/o/token/")
    hub_code = models.DeviceCode.objects.get(secret=body["device_code"])
    assert hub_code.client.client_id == body["client_id"]
    assert hub_code.client.token_endpoint_auth_method == "none"


# --------------------------------------------------------------------------- #
# Start — logo download failure
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_start_logo_download_failure_returns_error(client, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    # download_logo is module-level in device_codes; the view turns the resulting
    # LogoDownloadError into the "Error downloading logo" envelope.
    monkeypatch.setattr(device_codes, "download_logo", _boom)

    body = _post(
        client,
        "app_authorization",
        {"manifest": _manifest(logo="https://example.com/logo.png")},
    ).json()

    assert body["status"] == "error"
    assert body["error"] == "Error downloading logo"


# --------------------------------------------------------------------------- #
# Hub claim
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_claim_hub_unknown_token_errors(client):
    # The view looks up a ``Hub`` and catches ``Hub.DoesNotExist``,
    # returning the dedicated not-found envelope rather than the generic
    # "Error creating configuration" fallthrough.
    body = _post(client, "fakts:hubclaim", {"token": "missing"}).json()
    assert body["status"] == "error"
    assert body["message"] == "No Hub found for this token"


# --------------------------------------------------------------------------- #
# Report (Bearer authenticated)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_report_without_bearer_token_is_401(client):
    resp = _post(client, "fakts:report", {"functional": False, "alias_reports": {}})
    assert resp.status_code == 401


@pytest.mark.django_db
def test_report_with_expired_bearer_token_is_401(client):
    fakts_client = factories.make_client()
    resp = _post(
        client,
        "fakts:report",
        {"functional": False, "alias_reports": {}},
        headers=_bearer_headers(fakts_client, exp_offset=-60),
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_report_with_unknown_client_id_is_401(client):
    fakts_client = factories.make_client()
    headers = _bearer_headers(fakts_client)
    fakts_client.delete()  # cascades onto the fakts client

    resp = _post(client, "fakts:report", {"functional": False, "alias_reports": {}}, headers=headers)
    assert resp.status_code == 401


@pytest.mark.django_db
def test_report_updates_functional_flag(client):
    fakts_client = factories.make_client()  # model default functional=True
    assert fakts_client.functional is True

    body = _post(
        client,
        "fakts:report",
        {"functional": False, "alias_reports": {}},
        headers=_bearer_headers(fakts_client),
    ).json()

    assert body["status"] == "reported"
    fakts_client.refresh_from_db()
    assert fakts_client.functional is False

"""Unhappy-path HTTP tests for the Fakts protocol endpoints (fakts/views.py).

Complements ``test_fakts_flows.py`` (which covers the happy paths) by exercising
the error branches: malformed bodies, expired/denied device codes, logo-download
failures, expired redeem tokens, rendering failures, and the claim/report error
envelopes — with emphasis on the claim endpoints.

Note: malformed requests return **HTTP 200** with a ``{"status": "error"}`` body
(``_parse`` builds a default-status ``JsonResponse``), so assertions are on the
JSON body, not the status code — except the explicit 405 (wrong-method) case.
"""

import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from fakts import models
from fakts.services import clients, device_codes, rendering
from tests import factories


def _post(client, name, payload):
    return client.post(reverse(name), data=json.dumps(payload), content_type="application/json")


def _manifest(version="1.0.0", **extra):
    return {"identifier": "com.example.errors", "version": version, "scopes": [], "requirements": [], **extra}


# --------------------------------------------------------------------------- #
# Malformed bodies / wrong method
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_start_malformed_json_returns_error(client):
    # Body is not valid JSON -> json.loads raises -> malformed envelope (key "error").
    resp = client.post(reverse("fakts:start"), data="{not json", content_type="application/json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert body["error"].startswith("Malformed request")


@pytest.mark.django_db
def test_redeem_missing_manifest_returns_error(client):
    # Valid JSON but missing the required ``manifest`` field -> pydantic validation
    # fails inside _parse -> malformed envelope (key "error").
    body = _post(client, "fakts:redeem", {"token": "whatever"}).json()
    assert body["status"] == "error"
    assert body["error"].startswith("Malformed request")


@pytest.mark.django_db
def test_claim_missing_token_uses_message_error_key(client):
    # ClaimView passes error_key="message", so the malformed envelope uses "message".
    body = _post(client, "fakts:claim", {"secure": False}).json()
    assert body["status"] == "error"
    assert body["message"].startswith("Malformed request")


@pytest.mark.django_db
def test_get_on_post_only_view_returns_405(client):
    resp = client.get(reverse("fakts:claim"))
    assert resp.status_code == 405


# --------------------------------------------------------------------------- #
# Device-code challenge endpoints (_poll_device_code)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_challenge_expired_code_returns_expired_and_deletes(client):
    device_code = factories.make_device_code(expires_at=timezone.now() - timedelta(seconds=1))

    body = _post(client, "fakts:challenge", {"code": device_code.code}).json()

    assert body["status"] == "expired"
    assert not models.DeviceCode.objects.filter(code=device_code.code).exists()


@pytest.mark.django_db
def test_challenge_denied_code_returns_denied_and_deletes(client):
    device_code = factories.make_device_code(denied=True)

    body = _post(client, "fakts:challenge", {"code": device_code.code}).json()

    assert body["status"] == "denied"
    assert not models.DeviceCode.objects.filter(code=device_code.code).exists()


@pytest.mark.django_db
def test_service_challenge_unknown_code_errors(client):
    body = _post(client, "fakts:servicechallenge", {"code": "does-not-exist"}).json()
    assert body["status"] == "error"
    assert body["error"] == "Challenge does not exist"


@pytest.mark.django_db
def test_composition_challenge_unknown_code_errors(client):
    body = _post(client, "fakts:compositionchallenge", {"code": "does-not-exist"}).json()
    assert body["status"] == "error"
    assert body["error"] == "Challenge does not exist"


# --------------------------------------------------------------------------- #
# Service / Composition start (currently untested) + their challenge routes
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_service_start_returns_code_and_challenge(client):
    body = _post(
        client,
        "fakts:servicestart",
        {"manifest": {"identifier": "com.example.svc", "version": "1.0.0"}},
    ).json()
    assert body["status"] == "granted"
    assert body["code"]
    assert body["challenge"]
    assert models.ServiceDeviceCode.objects.filter(challenge_code=body["challenge"]).exists()


@pytest.mark.django_db
def test_composition_start_returns_code_and_challenge(client):
    body = _post(
        client,
        "fakts:compositionstart",
        {"composition": {"identifier": "com.example.comp"}},
    ).json()
    assert body["status"] == "granted"
    assert body["code"]
    assert body["challenge"]
    assert models.CompositionDeviceCode.objects.filter(challenge_code=body["challenge"]).exists()


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
        "fakts:start",
        {"manifest": _manifest(logo="https://example.com/logo.png")},
    ).json()

    assert body["status"] == "error"
    assert body["error"] == "Error downloading logo"


# --------------------------------------------------------------------------- #
# Retrieve
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_retrieve_unknown_app_errors(client):
    body = _post(
        client,
        "fakts:retrieve",
        {"manifest": {"identifier": "com.example.nope", "version": "1.0.0", "scopes": []}},
    ).json()
    assert body["status"] == "error"
    assert body["message"].startswith("App does not exist") or body["message"].startswith("Release does not exist")


# --------------------------------------------------------------------------- #
# Redeem
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_redeem_expired_token_returns_error_and_deletes(client):
    redeem = factories.make_redeem_token(expires_at=timezone.now() - timedelta(seconds=1))

    body = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest()}).json()

    assert body["status"] == "error"
    assert body["message"] == "Redeem token expired"
    # The expired token is deleted; redeem_token() removes it outside the atomic
    # block so the deletion commits rather than being rolled back by the raise.
    assert not models.RedeemToken.objects.filter(pk=redeem.pk).exists()


@pytest.mark.django_db
def test_redeem_generic_exception_returns_error(client, monkeypatch):
    def _boom(*args, **kwargs):
        raise ValueError("kaboom")

    # The view's catch-all ``except Exception`` surfaces the message verbatim.
    monkeypatch.setattr(clients, "redeem_token", _boom)

    body = _post(client, "fakts:redeem", {"token": "anything", "manifest": _manifest()}).json()

    assert body["status"] == "error"
    assert body["message"] == "kaboom"


# --------------------------------------------------------------------------- #
# Claim (emphasis)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_claim_rendering_failure_returns_error(client, monkeypatch):
    fakts_client = factories.make_client()

    def _boom(*args, **kwargs):
        raise RuntimeError("render exploded")

    monkeypatch.setattr(rendering, "render_composition", _boom)

    body = _post(client, "fakts:claim", {"token": fakts_client.token, "secure": False}).json()

    assert body["status"] == "error"
    assert body["message"] == "Error creating configuration"


@pytest.mark.django_db
def test_claim_composition_unknown_token_errors(client):
    # The view looks up a ``Composition`` and catches ``Composition.DoesNotExist``,
    # returning the dedicated not-found envelope rather than the generic
    # "Error creating configuration" fallthrough.
    body = _post(client, "fakts:compositionclaim", {"token": "missing"}).json()
    assert body["status"] == "error"
    assert body["message"] == "No Composition found for this token"


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_report_unknown_token_errors(client):
    body = _post(client, "fakts:report", {"token": "missing"}).json()
    assert body["status"] == "error"
    assert body["message"] == "No Client found for this token"


@pytest.mark.django_db
def test_report_updates_functional_flag(client):
    fakts_client = factories.make_client()  # model default functional=True
    assert fakts_client.functional is True

    body = _post(
        client,
        "fakts:report",
        {"token": fakts_client.token, "functional": False, "alias_reports": {}},
    ).json()

    assert body["status"] == "reported"
    fakts_client.refresh_from_db()
    assert fakts_client.functional is False

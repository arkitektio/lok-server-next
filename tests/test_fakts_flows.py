"""End-to-end HTTP tests for the Fakts protocol endpoints (fakts/views.py)."""

import json

import pytest
from django.urls import reverse

from fakts import models
from tests import factories


def _post(client, name, payload):
    return client.post(reverse(name), data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_start_then_challenge_pending_then_granted(client):
    # start: stage a device code
    resp = _post(
        client,
        "fakts:start",
        {
            "manifest": {"identifier": "com.example.flow", "version": "1.0.0", "scopes": [], "requirements": []},
            "requested_client_kind": "development",
            "requested_client_role": "agent",
        },
    )
    body = resp.json()
    assert body["status"] == "granted"
    code = body["code"]

    device_code = models.DeviceCode.objects.get(code=code)
    assert device_code.staging_role == "agent"

    # challenge before approval -> pending
    pending = _post(client, "fakts:challenge", {"code": code}).json()
    assert pending["status"] == "pending"

    # simulate approval by attaching a client, then challenge -> granted
    fakts_client = factories.make_client()
    device_code.client = fakts_client
    device_code.save()

    granted = _post(client, "fakts:challenge", {"code": code}).json()
    assert granted["status"] == "granted"
    assert granted["token"] == fakts_client.token


@pytest.mark.django_db
def test_challenge_unknown_code_errors(client):
    body = _post(client, "fakts:challenge", {"code": "does-not-exist"}).json()
    assert body["status"] == "error"
    assert body["error"] == "Challenge does not exist"


@pytest.mark.django_db
def test_retrieve_returns_public_client_token(client):
    app = factories.make_app(identifier="com.example.public")
    release = factories.make_release(app=app, version="2.0.0")
    public_client = factories.make_client(release=release, public=True)

    body = _post(
        client,
        "fakts:retrieve",
        {"manifest": {"identifier": "com.example.public", "version": "2.0.0", "scopes": []}},
    ).json()

    assert body["status"] == "granted"
    assert body["token"] == public_client.token


@pytest.mark.django_db
def test_retrieve_without_public_client_errors(client):
    app = factories.make_app(identifier="com.example.private")
    factories.make_release(app=app, version="1.0.0")

    body = _post(
        client,
        "fakts:retrieve",
        {"manifest": {"identifier": "com.example.private", "version": "1.0.0", "scopes": []}},
    ).json()
    assert body["status"] == "error"


@pytest.mark.django_db
def test_redeem_creates_client(client):
    composition = factories.make_composition()
    redeem = factories.make_redeem_token(composition=composition)

    body = _post(
        client,
        "fakts:redeem",
        {
            "token": redeem.token,
            "manifest": {"identifier": "com.example.redeemed", "version": "1.0.0", "scopes": [], "requirements": []},
        },
    ).json()

    assert body["status"] == "granted"
    redeem.refresh_from_db()
    assert redeem.client is not None
    assert body["token"] == redeem.client.token


@pytest.mark.django_db
def test_redeem_unknown_token_errors(client):
    body = _post(
        client,
        "fakts:redeem",
        {"token": "nope", "manifest": {"identifier": "x", "version": "1.0.0", "scopes": [], "requirements": []}},
    ).json()
    assert body["status"] == "error"
    assert body["message"] == "Invalid redeem token"


def _manifest(version="1.0.0"):
    return {"identifier": "com.example.redeemed", "version": version, "scopes": [], "requirements": []}


@pytest.mark.django_db
def test_redeem_same_manifest_twice_returns_same_client(client):
    redeem = factories.make_redeem_token()

    first = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest()}).json()
    second = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest()}).json()

    assert first["status"] == "granted"
    assert second["status"] == "granted"
    assert first["token"] == second["token"]


@pytest.mark.django_db
def test_redeem_changed_manifest_rejected_without_allow_reredeem(client):
    redeem = factories.make_redeem_token()

    _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("1.0.0")})
    body = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("2.0.0")}).json()

    assert body["status"] == "error"
    assert "allow_reredeem" in body["message"]


@pytest.mark.django_db
def test_redeem_changed_manifest_allowed_with_reredeem(client):
    redeem = factories.make_redeem_token(allow_reredeem=True)

    _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("1.0.0")})
    body = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("2.0.0")}).json()

    assert body["status"] == "granted"


@pytest.mark.django_db
def test_redeem_grandfathers_null_manifest_hash(client):
    redeem = factories.make_redeem_token()

    _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("1.0.0")})

    # Simulate a token redeemed before manifest-hash tracking existed.
    models.RedeemToken.objects.filter(pk=redeem.pk).update(manifest_hash=None)

    # A changed manifest is accepted (and the hash backfilled), not rejected.
    body = _post(client, "fakts:redeem", {"token": redeem.token, "manifest": _manifest("3.0.0")}).json()
    assert body["status"] == "granted"

    redeem.refresh_from_db()
    assert redeem.manifest_hash is not None


@pytest.mark.django_db
def test_claim_returns_config(client):
    fakts_client = factories.make_client()

    body = _post(client, "fakts:claim", {"token": fakts_client.token, "secure": False}).json()

    assert body["status"] == "granted"
    assert body["config"]["auth"]["client_id"] == fakts_client.oauth2_client.client_id


@pytest.mark.django_db
def test_claim_unknown_token_errors(client):
    body = _post(client, "fakts:claim", {"token": "missing"}).json()
    assert body["status"] == "error"
    assert body["message"] == "No Client found for this token"

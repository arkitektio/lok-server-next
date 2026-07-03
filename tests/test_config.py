"""Validate the lok service's config.yaml against its bespoke schema.

Standalone — needs no database; run with ``uv run pytest tests/test_config.py``.
"""

import pytest
from pydantic import ValidationError

from lok_server.configuration import AccountSettings, Settings


def test_config_yaml_validates():
    """The service's own config.yaml parses into the typed schema."""
    s = Settings()
    assert s.postgres.db_name
    assert s.redis.host


def test_env_override(monkeypatch):
    """Env vars override the YAML file (nested via ``__``)."""
    monkeypatch.setenv("POSTGRES__PASSWORD", "from-env-test")
    assert Settings().postgres.password == "from-env-test"


def test_signup_fields_derived_from_login_methods():
    """When signup_fields is omitted it is derived from login_methods."""
    assert AccountSettings().signup_fields == ["username*", "password1*", "password2*"]
    assert AccountSettings(login_methods=["email"]).signup_fields == [
        "email*",
        "password1*",
        "password2*",
    ]


def test_email_login_requires_email_signup_field():
    """Email login paired with a signup form that never collects an email fails."""
    with pytest.raises(ValidationError, match="email"):
        AccountSettings(login_methods=["email"], signup_fields=["username*", "password1*", "password2*"])


def test_mandatory_verification_requires_smtp_block():
    """Mandatory email verification without an `email:` SMTP block fails fast."""
    with pytest.raises(ValidationError, match="mandatory"):
        Settings(account={"email_verification": "mandatory"})


def test_social_provider_config_dumps_to_allauth_shape():
    """A typed provider entry round-trips to exactly the dict allauth expects,
    preserving provider-specific extras and dropping unset optionals."""
    s = Settings(socialaccount_providers={
        "google": {
            "APP": {"client_id": "gid", "secret": "gsecret"},
            "SCOPE": ["profile", "email"],
            "FETCH_USERINFO": True,  # provider-specific extra
        }
    })
    dumped = {p: c.model_dump(exclude_none=True) for p, c in s.socialaccount_providers.items()}
    assert dumped == {
        "google": {
            "APP": {"client_id": "gid", "secret": "gsecret", "key": "", "settings": {}},
            "SCOPE": ["profile", "email"],
            "FETCH_USERINFO": True,
        }
    }


def test_social_provider_rejects_bad_app_credentials():
    """A missing/mistyped APP credential key is caught at load time."""
    with pytest.raises(ValidationError):
        Settings(socialaccount_providers={"google": {"APP": {"clientid": "typo"}}})

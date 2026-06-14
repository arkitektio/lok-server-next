from .settings import *  # noqa
from .settings import DATABASES, AUTHENTIKATE
import logging

DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3", 
    "NAME": ":memory:",
    "OPTIONS": {
        "timeout": 30,
    },
    "TEST": {
        "NAME": ":memory:",
    }
}


AUTHENTIKATE = {**AUTHENTIKATE, "STATIC_TOKENS": {"test": {"sub": "1", "active_org": "testorg"}}}

# Never touch the real ionscale CLI in tests: build the in-memory fake by default.
# The ``_reset_ionscale_repo`` autouse fixture rebuilds it fresh per test.
IONSCALE_REPOSITORY = "ionscale.testing.FakeIonscaleRepository"
# Don't fail-fast / eagerly build the repo at boot during tests.
IONSCALE_EAGER_INIT = False

# Disable migrations for faster tests
class DisableMigrations:
    """Disable migrations during testing for faster test execution."""
    
    def __contains__(self, item: str) -> bool:
        """Check if item is in migration modules."""
        return True
    
    def __getitem__(self, item: str) -> None:
        """Get migration module for item."""
        return None

# For faster test execution, you can uncomment this:
# MIGRATION_MODULES = DisableMigrations()

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)

# Enable database access from async code in tests
DATABASE_ROUTERS = []

# Use in-memory channel layer for tests instead of Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

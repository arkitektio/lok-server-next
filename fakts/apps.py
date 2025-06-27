from django.apps import AppConfig


class FaktsConfig(AppConfig):
    """Configuration class for the Fakts which allows service
    discover and management."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fakts"

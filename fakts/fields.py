from django.db import models
import logging


logger = logging.getLogger(__name__)


def validate_semver(version: str):
    return True


class VersionField(models.CharField):
    default_validators = [validate_semver]

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 1000
        super().__init__(*args, **kwargs)


def validate_app_identifier(name: str):
    return True


class IdentifierField(models.CharField):
    default_validators = [validate_app_identifier]

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 1000
        super().__init__(*args, **kwargs)


class S3ImageField(models.CharField):
    pass

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 1000
        kwargs["null"] = True
        kwargs["blank"] = True
        super().__init__(*args, **kwargs)

    def save(self, name: str, *args, **kwargs):
        logger.error("Not implemented")
        return super().save(name)

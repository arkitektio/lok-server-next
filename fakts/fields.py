from django.db import models
import logging
from django.conf import settings
from karakter.datalayer import Datalayer
from django.core.cache import cache
from django.db import models
from django.core.exceptions import ValidationError
import re

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




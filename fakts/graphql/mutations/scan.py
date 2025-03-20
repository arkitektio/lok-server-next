import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from ekke.types import Info

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest
from fakts.builders import create_client
from fakts.scan import scan

logger = logging.getLogger(__name__)


def scan_backend(info: Info, input: inputs.ScanBackendInput) -> str:

    token = scan()

    return token

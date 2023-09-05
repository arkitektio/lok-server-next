from enum import Enum
import strawberry
from django.db.models import TextChoices


class ClientKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    WEBSITE = "website", "WEBSITE (Value represent WEBSITE)"
    DEVELOPMENT = "development", "DEVELOPMENT (Value represent DEVELOPMENT)"
    DESKTOP = "desktop", "DESKTOP (Value represent DESKTOP Aüü)"


@strawberry.enum
class ClientKind(str, Enum):
    DEVELOPMENT = "development"
    WEBSITE = "website"
    DESKTOP = "desktop"


class FilterKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    HOST_REGEX = "host_regex", "Host matches regex"
    HOST_IS = "host_is", "Host is"
    HOST_IS_NOT = "host_is_not", "Host is not"
    PORT_IS = "port_is", "Port is"
    PORT_IS_NOT = "port_is_not", "Port is not"
    VERSION_IS = "version_is", "Version is"
    VERSION_IS_NOT = "version_is_not", "Version is not"
    VERSION_REGEX = "version_regex", "Version matches regex"
    IDENTIFIER_IS = "identifier_is", "Identifier is"
    IDENTIFIER_IS_NOT = "identifier_is_not", "Identifier is not"
    IDENTIFIER_REGEX = "identifier_regex", "Identifier matches regex"
    USER_IS = "user_is", "Checks if user is certain id"
    USER_IS_DEVELOPER = "user_is_developer", "Checks if the user is developer"


@strawberry.enum
class FilterKind(str, Enum):
    HOST_REGEX = "host_regex"
    HOST_IS = "host_is"
    HOST_IS_NOT = "host_is_not"
    PORT_IS = "port_is"
    PORT_IS_NOT = "port_is_not"
    VERSION_IS = "version_is"
    VERSION_IS_NOT = "version_is_not"
    VERSION_REGEX = "version_regex"
    IDENTIFIER_IS = "identifier_is"
    IDENTIFIER_IS_NOT = "identifier_is_not"
    IDENTIFIER_REGEX = "identifier_regex"
    USER_IS = "user_is"
    USER_IS_DEVELOPER = "user_is_developer"


class FaktsGrantKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    RETRIEVE = "retrieve", "RETRIEVE (Value represent RETRIEVE)"
    DEVICE_CODE = "device_code", "DEVICE_CODE (Value represent DEVICE_CODE)"


@strawberry.enum
class FaktsGrantKind(str, Enum):
    RETRIEVE = "retrieve"
    DEVICE_CODE = "device_code"

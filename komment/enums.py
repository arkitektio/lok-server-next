from enum import Enum
import strawberry
from django.db.models import TextChoices



@strawberry.enum
class DescendantKind(str, Enum):
    """Event Type for the Event Operator"""

    LEAF = "LEAF"
    MENTION = "MENTION"
    PARAGRAPH = "PARAGRAPH"


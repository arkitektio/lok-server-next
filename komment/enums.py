from enum import Enum
import strawberry
from django.db.models import TextChoices



@strawberry.enum(description="The Kind of a Descendant")
class DescendantKind(str, Enum):
    """The Kind of a Descendant

    Determines the type of rich rendering that should be applied to the descendant

    
    """

    LEAF = strawberry.enum_value(
        "LEAF", description="A leaf of text."
    )
    MENTION = strawberry.enum_value(
        "MENTION", description="A mention of a user"
    )
    PARAGRAPH = strawberry.enum_value(
        "PARGRAPTH", description="A Paragraph of text"
    )


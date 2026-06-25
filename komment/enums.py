from enum import Enum
import strawberry


@strawberry.enum(description="The Kind of a Descendant")
class DescendantKind(str, Enum):
    """The Kind of a Descendant

    Determines the type of rich rendering that should be applied to the descendant


    """

    LEAF = "LEAF"
    MENTION = "MENTION"
    PARAGRAPH = "PARAGRAPH"

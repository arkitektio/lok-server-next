from typing import NewType
import strawberry


ExtraData = strawberry.scalar(
    NewType("ExtraData", object),
    description="The `ArrayLike` scalasr typsse represents a reference to a store previously created by the user n a datalayer",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

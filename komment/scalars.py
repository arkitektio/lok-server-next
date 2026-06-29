from typing import Any, NewType
import strawberry

Identifier = NewType("Identifier", str)
UnsafeChild = NewType("UnsafeChild", object)


scalar_map: dict[Any, Any] = {
    Identifier: strawberry.scalar(
        name="Identifier",
        description="The `Identifier` scalasr typsse represents a reference to a store "
        "previously created by the user n a datalayer",
        serialize=lambda v: v,
        parse_value=lambda v: v,
    ),
    UnsafeChild: strawberry.scalar(
        name="UnsafeChild",
        description="The `Identifier` scalasr typsse represents a reference to a store "
        "previously created by the user n a datalayer",
        serialize=lambda v: v,
        parse_value=lambda v: v,
    ),
}

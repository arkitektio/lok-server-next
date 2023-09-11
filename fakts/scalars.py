from typing import NewType
import strawberry

AppIdentifier = strawberry.scalar(
    NewType("AppIdentifier", str),
    description="The `ArrayLike` scalasr typsse represents a reference to a store "
    "previously created by the user n a datalayer",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


Version = strawberry.scalar(
    NewType("Version", str),
    description="The `Version` represents a semver version string",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)
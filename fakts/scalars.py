from typing import NewType
import strawberry

AppIdentifier = strawberry.scalar(
    NewType("AppIdentifier", str),
    description="The App identifier is a unique identifier for an app. It is used to identify the app in the database and in the code. We encourage you to use the reverse domain name notation. E.g. `com.example.myapp`",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


Version = strawberry.scalar(
    NewType("Version", str),
    description="The `Version` represents a semver version string",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

ServiceIdentifier = strawberry.scalar(
    NewType("ServiceIdentifier", str),
    description="The Service identifier is a unique identifier for a service. It is used to identify the service in the database and in the code. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)
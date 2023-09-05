from ekke.types import Info
from typing import AsyncGenerator
from typing import Any, Type
import strawberry_django
import strawberry
from ekke.directives import upper, replace, relation
from strawberry_django.optimizer import DjangoOptimizerExtension
from karakter.graphql.mutations import create_user
from karakter.graphql import queries as karakter_queries
from karakter.graphql.subscriptions import communications
from fakts import types as fakts_types
from karakter import types as karakter_types
from komment import types as komment_types
from komment.graphql import mutations as komment_mutations
from komment.graphql import queries as komment_queries

@strawberry.type
class Query:
    apps: list[fakts_types.App] = strawberry_django.field()
    releases: list[fakts_types.Release] = strawberry_django.field()
    clients: list[fakts_types.Client] = strawberry_django.field()
    compositions: list[fakts_types.Composition] = strawberry_django.field()
    users: list[karakter_types.User] = strawberry_django.field()
    comments: list[komment_types.Comment] = strawberry_django.field()

    user = strawberry_django.field(resolver=karakter_queries.user)



    @strawberry_django.field()
    def hallo(self, info: Info) -> str:
        print("hallo")
        return "hallo"


@strawberry.type
class Mutation:
    create_user = strawberry_django.mutation(
        resolver=create_user,
    )
    create_comment = strawberry_django.mutation(
        resolver=komment_mutations.create_comment,
    )


@strawberry.type
class Subscription:
    communication = strawberry.subscription(resolver=communications)


schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    mutation=Mutation,
    directives=[upper, replace, relation],
    extensions=[
        DjangoOptimizerExtension,
    ],
    types=[
        komment_types.Descendant,
        komment_types.MentionDescendant,
        komment_types.LeafDescendant,
    ]  # We really need to register
    # all the types here, otherwise the schema will not be able to resolve them
    # and will throw a cryptic error
)

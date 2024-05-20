import strawberry

@strawberry.input
class CreateStashInput:
    name: str | None = None
    description: str | None = None

@strawberry.input
class DeleteStashInput:
    stash: strawberry.ID

@strawberry.input
class StashItemInput:
    identifier: str
    description: str | None = None
    object: str


@strawberry.input
class AddItemToStashInput:
    stash: strawberry.ID
    items: list[StashItemInput]

@strawberry.input
class RemoveItemsFromStashInput:
    stash: strawberry.ID
    items: list[StashItemInput]

@strawberry.input
class DeleteStashItems:
    items: list[strawberry.ID]



@strawberry.input
class UpdateStashInput:
    stash: strawberry.ID
    name: str
    description: str | None = None
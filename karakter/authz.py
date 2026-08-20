"""Object-level authorization helpers for the **main** (`/graphql`) schema.

`api.management.authz` does this job for the management endpoint. That endpoint
authenticates by session and scopes to "any organization the caller is a member
of". This module is its counterpart for the token-authenticated main schema,
which speaks a different dialect: the caller's organization is the one named by
their JWT's `active_org` claim, resolved onto the request by
`authapp.extension.AuthAppExtension` — which already refuses to resolve a
membership the user does not hold. So `request.organization` is a *trusted*
value here, and scoping to it is the correct tenant boundary.

Several resolvers on this schema fetched by bare pk and never read `info` at
all, letting any principal mutate any tenant's objects. These helpers exist so a
guard is one line, matching the ergonomics of the management side.
"""

from graphql import GraphQLError

# Deliberately identical to `api.management.authz.DENIED` so a denial cannot be
# distinguished from a genuine not-found and used as an existence oracle.
DENIED = "Not found, or you are not authorized to access it."


def get_user(info):
    """Return the authenticated caller, or fail closed.

    kante's `UniversalRequest.user` *raises* when no principal was set rather
    than returning None, so this is a try/except rather than a getattr default.
    """
    try:
        user = info.context.request.user
    except Exception:
        raise GraphQLError(DENIED)
    if user is None or not getattr(user, "is_authenticated", False):
        raise GraphQLError(DENIED)
    return user


def get_organization(info):
    """Return the caller's active organization, or fail closed.

    Resolved from the token's `active_org` claim, and already validated against
    the caller's memberships by `AuthAppExtension`.
    """
    try:
        organization = info.context.request.organization
    except Exception:
        raise GraphQLError(DENIED)
    if organization is None:
        raise GraphQLError(DENIED)
    return organization


def get_scoped_or_denied(manager, info, field="organization", **lookup):
    """Fetch a single object, narrowed to the caller's organization.

    Returns the object, or raises the uniform `DENIED` error if it does not
    exist *or* belongs to another tenant — the two cases are deliberately
    indistinguishable to the caller.
    """
    organization = get_organization(info)
    try:
        return manager.get(**{field: organization}, **lookup)
    except manager.model.DoesNotExist:
        raise GraphQLError(DENIED)


def assert_owns_object(info, obj, field="organization"):
    """Require that ``obj`` belongs to the caller's active organization."""
    organization = get_organization(info)
    if getattr(obj, f"{field}_id", None) != organization.id:
        raise GraphQLError(DENIED)


def assert_is_self(info, user_id):
    """Require that ``user_id`` is the calling user (for per-user objects)."""
    user = get_user(info)
    if str(user_id) != str(user.id):
        raise GraphQLError(DENIED)


def resolve_own_media_store(info, media_store_id, model):
    """Resolve a `MediaStore` the caller is entitled to attach.

    Uploads are namespaced under `users/{user.id}/` by `request_media_upload`, so
    ownership is read off the key prefix — without this, an arbitrary pk let you
    attach someone else's media to your profile.

    Deliberately tolerant of *legacy* keys: namespacing only started with this
    change, so every row created before it has an unprefixed key and belongs to
    nobody in particular. Rejecting those would break editing for every existing
    profile. So the rule is "not namespaced to a **different** user" rather than
    "namespaced to me" — which still blocks the actual attack (pointing at
    another user's upload) while leaving old rows usable.
    """
    user = get_user(info)
    try:
        store = model.objects.get(pk=media_store_id)
    except model.DoesNotExist:
        raise GraphQLError(DENIED)

    key = store.key or ""
    if key.startswith("users/") and not key.startswith(f"users/{user.id}/"):
        raise GraphQLError(DENIED)
    return store

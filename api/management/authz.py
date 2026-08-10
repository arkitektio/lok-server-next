"""Object-level authorization helpers for management query resolvers.

The single-object query resolvers historically fetched by primary key with a bare
``Model.objects.get(id=id)`` and therefore skipped the per-user ``get_queryset``
filter that the corresponding list fields apply. That let an authenticated user
read any object across tenants (IDOR). ``get_scoped`` routes a single-object
lookup through the same type-level ``get_queryset`` so the object is only
returned when the caller is allowed to see it, and returns a not-found error
otherwise (rather than leaking existence).
"""

from graphql import GraphQLError

# Reused for every authorization denial. Deliberately identical to the not-found
# message so a caller cannot use the error text to probe whether an id exists in
# another tenant (an existence oracle).
DENIED = "Not found, or you are not authorized to access it."


def get_user(info):
    """Return the authenticated caller.

    ``RequireAuthenticationExtension`` already rejects anonymous callers on every
    non-public root field, so this is a belt-and-braces read that fails closed if
    a resolver is ever reached without a principal.
    """
    request = getattr(info.context, "request", None)
    try:
        user = request.user if request is not None else None
    except Exception:
        user = None
    if user is None or not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required to access the management API.")
    return user


def assert_member(info, organization) -> None:
    """Require that the caller belongs to ``organization``.

    ``organization`` is ``None`` for objects that hang off a *global* (org-less)
    parent — e.g. ``ServiceInstance.organization`` is nullable for instances shared
    across tenants. Those are deliberately not editable through this endpoint: an
    org-less object belongs to no tenant, so no tenant member may claim it. Fail
    closed rather than dereferencing ``None`` (a 500) or filtering on it (which
    would match and *allow*).
    """
    if organization is None:
        raise GraphQLError(DENIED)
    user = get_user(info)
    if not organization.memberships.filter(user=user).exists():
        raise GraphQLError(DENIED)


def assert_owner(info, organization) -> None:
    """Require that the caller owns ``organization``."""
    if organization is None:
        raise GraphQLError(DENIED)
    if organization.owner_id != get_user(info).id:
        raise GraphQLError(DENIED)


def assert_owner_or_admin(info, organization) -> None:
    """Require that the caller owns ``organization`` or holds its ``admin`` role.

    This is the bar for privileged operations (role grants, deletes, minting
    credentials) as opposed to ordinary membership.
    """
    if organization is None:
        raise GraphQLError(DENIED)
    user = get_user(info)
    if organization.owner_id == user.id:
        return
    if organization.memberships.filter(user=user, roles__identifier="admin").exists():
        return
    raise GraphQLError(DENIED)


def get_scoped(type_cls, queryset, info):
    """Return the single object in ``queryset`` visible to the caller.

    ``type_cls`` is the strawberry-django type whose ``get_queryset(qs, info)``
    encodes the tenant-scoping policy. If the type has no such method the
    queryset is used as-is. Raises if nothing visible matches.
    """
    get_queryset = getattr(type_cls, "get_queryset", None)
    if get_queryset is not None:
        queryset = get_queryset(queryset, info)

    obj = queryset.first()
    if obj is None:
        raise GraphQLError("Not found, or you are not authorized to access it.")
    return obj

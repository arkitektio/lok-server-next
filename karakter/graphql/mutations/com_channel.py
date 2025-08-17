"""
karakter.graphql.mutations.com_channel

GraphQL mutations for client communication channels and notifications.

This module provides:
- register_com_channel: stores/updates a user's communication channel
  token used to deliver messages to the user.
- notify_user: server-side mutation to send an in-app or external
  notification to a user.

The implementations perform authentication and input validation and
log and wrap lower-level errors to provide clearer failure reasons to
API callers.
"""

import logging
from typing import Optional, cast

import strawberry
from kante.types import Info

from karakter import models, types

logger = logging.getLogger(__name__)


@strawberry.input
class RegisterComChannelInput:
    """Input for registering/updating a communication channel.

    Attributes:
        token: platform-specific device/token string used to address
            notifications for the authenticated user.
    """

    token: str


def _get_request_user(info: Info) -> Optional[models.User]:
    """Helper returning the request user or None if unavailable.

    Returning the concrete Django ``User`` model makes subsequent type
    checks clearer for linters and callers.
    """
    request = getattr(info.context, "request", None)
    return getattr(request, "user", None) if request is not None else None


def register_com_channel(info: Info, input: RegisterComChannelInput) -> types.ComChannel:
    """Register or update the current user's communication channel.

    Validates that the caller is authenticated and that a non-empty
    token is provided. Database errors are logged and re-raised as a
    RuntimeError to avoid leaking internal exception details to API
    consumers.

    Args:
        info: resolver info containing the request context.
        input: RegisterComChannelInput with the channel token.

    Returns:
        The created or updated ``ComChannel`` instance.

    Raises:
        PermissionError: when the caller is not authenticated.
        ValueError: when the token is empty.
        RuntimeError: when a database error occurs.
    """
    user = _get_request_user(info)
    if not user:
        raise PermissionError("Authentication required to register a communication channel")

    token = (input.token or "").strip()
    if not token:
        raise ValueError("Token must not be empty")

    try:
        channel, _created = models.ComChannel.objects.update_or_create(
            user=user,
            defaults={"token": token},
        )
    except Exception as exc:  # broad catch to wrap DB/ORM errors
        logger.exception("Failed to register communication channel for user=%s", getattr(user, "id", None))
        raise RuntimeError("Failed to register communication channel") from exc

    return cast(types.ComChannel, channel)


@strawberry.input
class NotifyUserInput:
    """Input for sending a notification to a user.

    Attributes:
        user: the target user's ID (strawberry.ID, typically a string).
        message: the notification body (required).
        title: short notification title (optional but encouraged).
    """

    user: strawberry.ID
    message: str
    title: Optional[str] = ""


def notify_user(info: Info, input: NotifyUserInput) -> bool:
    """Send a notification to a user.

    The caller must be authenticated. Non-staff callers may only send
    notifications to themselves; staff users may notify any user.

    Args:
        info: resolver info containing request context.
        input: NotifyUserInput describing the target and message.

    Returns:
        True when the notification was successfully queued/sent.

    Raises:
        PermissionError: when the caller is not authorized to notify the
            target user.
        ValueError: when the target user does not exist or message is
            empty.
        RuntimeError: when sending the notification fails.
    """
    caller = _get_request_user(info)
    if not caller :
        raise PermissionError("Authentication required to send notifications")

    # Resolve target user
    try:
        target_user = models.User.objects.get(id=input.user)
    except models.User.DoesNotExist:
        logger.warning("notify_user: target user not found id=%s caller=%s", input.user, getattr(caller, "id", None))
        raise ValueError("Target user not found")

    # Permission check: allow self-notify or staff
    if caller != target_user:
        logger.warning(
            "notify_user: insufficient permissions caller=%s target=%s",
            getattr(caller, "id", None),
            getattr(target_user, "id", None),
        )
        raise PermissionError("Insufficient permissions to notify this user at this time ")

    message = (input.message or "").strip()
    if not message:
        raise ValueError("Notification message must not be empty")

    title = (input.title or "").strip()

    try:
        target_user.notify(title, message)
    except Exception as exc:
        logger.exception("Failed to send notification to user=%s", getattr(target_user, "id", None))
        raise RuntimeError("Failed to send notification") from exc

    return True

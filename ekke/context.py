from strawberry.channels import ChannelsConsumer, ChannelsRequest
from strawberry.http.temporal_response import TemporalResponse
from dataclasses import dataclass
from typing import Any, Dict, Optional
from oauth2_provider.models import Application
from django.contrib.auth import get_user_model


User = get_user_model()


@dataclass
class EnhancendChannelsHTTPRequest(ChannelsRequest):
    """An ehanced version of Channels' HTTP Request that
    includes user, app, scopes and assignation_id from the
    headers."""

    user: Optional[User] = None
    app: Optional[Application] = None
    scopes: Optional[list[str]] = None
    assignation_id: Optional[str] = None
    is_session: bool = False

    def has_scopes(self, scopes: list[str]) -> bool:
        if self.is_session:
            return True

        if self.scopes is None:
            return False

        return all(scope in self.scopes for scope in scopes)


@dataclass
class ChannelsContext:
    request: EnhancendChannelsHTTPRequest
    response: TemporalResponse

    @property
    def session(self):
        # Depends on Channels' SessionMiddleware / AuthMiddlewareStack
        if "session" in self.request.consumer.scope:
            return self.request.consumer.scope["session"]

        return None


@dataclass
class EnhancendChannelsWSRequest:
    user: Optional[User] = None
    app: Optional[Application] = None
    scopes: Optional[list[str]] = None
    assignation_id: Optional[str] = None


@dataclass
class ChannelsWSContext:
    """A context for websocket requests."""

    request: EnhancendChannelsWSRequest
    consumer: ChannelsConsumer
    connection_params: Optional[Dict[str, Any]] = None

    @property
    def ws(self) -> ChannelsConsumer:
        return self.request

"""
ASGI config for kreature project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""


import os

import django



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lok.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from django.core.asgi import get_asgi_application
from ekke.consumers import EkkeHTTPConsumer, EkkeWsConsumer
from ekke.cors import CorsMiddleware



# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from .schema import schema

gql_http_consumer = CorsMiddleware(
    AuthMiddlewareStack(EkkeHTTPConsumer.as_asgi(schema=schema))
)
gql_ws_consumer = EkkeWsConsumer.as_asgi(schema=schema)


websocket_urlpatterns = [
    re_path(r"graphql", gql_ws_consumer),
]

application = ProtocolTypeRouter(
    {
        "http": URLRouter(
            [
                re_path("^graphql", gql_http_consumer, name="graphql"),
                re_path(
                    "^", django_asgi_app
                ),  # This might be another endpoint in your app
            ]
        ),
        # Just HTTP for now. (We can add other protocols later.)
        "websocket": CorsMiddleware(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)

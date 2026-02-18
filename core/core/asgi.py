"""
ASGI config — wraps Django with Channels so WebSocket connections
are handled by Daphne / uvicorn alongside regular HTTP.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import users.routing  # WebSocket URL patterns live here

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Django HTTP application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Standard HTTP requests go to Django
    'http': django_asgi_app,

    # WebSocket connections are routed through Channels
    'websocket': AuthMiddlewareStack(
        URLRouter(
            users.routing.websocket_urlpatterns
        )
    ),
})

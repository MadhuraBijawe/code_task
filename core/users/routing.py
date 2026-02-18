"""
users/routing.py

WebSocket URL patterns consumed by core/asgi.py.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://host/ws/chat/
    re_path(r'^ws/chat/$', consumers.ChatConsumer.as_asgi()),
]

"""
users/consumers.py

WebSocket consumer for the real-time chat system.
All connected clients join the 'chat_room' group.
Messages sent by any client are broadcast to the entire group.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# NOTE: get_user_model() must NOT be called at module level here.
# This file is imported during ASGI startup (before Django apps are ready),
# so calling get_user_model() at import time raises ImproperlyConfigured.
# It is called lazily inside save_message() instead.

# All chat participants share a single group name
CHAT_GROUP = 'chat_room'


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket lifecycle:
      connect    — join the chat group
      disconnect — leave the chat group
      receive    — save message to DB and broadcast to group
      chat_message — send a message to the WebSocket client
    """

    async def connect(self):
        """Accept the WebSocket connection and join the chat group."""
        await self.channel_layer.group_add(CHAT_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the chat group on disconnect."""
        await self.channel_layer.group_discard(CHAT_GROUP, self.channel_name)

    async def receive(self, text_data):
        """
        Called when the client sends a message.
        Expects JSON: { "message": "...", "sender_id": <int> }
        Saves the message to the database (which triggers the post_save signal
        that also broadcasts — but we broadcast here directly for simplicity
        when the signal layer is not configured).
        """
        try:
            data = json.loads(text_data)
            content = data.get('message', '').strip()
            sender_id = data.get('sender_id')
        except (json.JSONDecodeError, KeyError):
            return  # Ignore malformed messages

        if not content:
            return

        # Persist the message (the post_save signal will also broadcast)
        sender_email = await self.save_message(sender_id, content)

        # Broadcast to all group members
        await self.channel_layer.group_send(
            CHAT_GROUP,
            {
                'type': 'chat_message',   # maps to the chat_message() handler below
                'message': content,
                'sender': sender_email or 'Anonymous',
            },
        )

    async def chat_message(self, event):
        """
        Handler called by the channel layer when a 'chat_message' event
        is dispatched to this group (either from receive() or from the
        post_save signal via signals.py).
        """
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

    # ── Database helpers (run in thread pool) ────────────────────────────────

    @database_sync_to_async
    def save_message(self, sender_id, content):
        """Save a Message record and return the sender's email."""
        # Lazy imports — safe to call here because Django is fully ready
        # by the time any WebSocket message is received.
        from django.contrib.auth import get_user_model
        from .models import Message

        User = get_user_model()
        try:
            sender = User.objects.get(pk=sender_id)
            Message.objects.create(sender=sender, content=content)
            return sender.email
        except User.DoesNotExist:
            return None

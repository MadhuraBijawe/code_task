"""
users/signals.py

Django signal: when a Message is saved (post_save), broadcast it
to the 'chat_room' WebSocket group via the channel layer.

This decouples the broadcast logic from the consumer — any code that
creates a Message (e.g. admin, management commands) will automatically
push it to connected WebSocket clients.
"""

import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Message

CHAT_GROUP = 'chat_room'


@receiver(post_save, sender=Message)
def broadcast_message(sender, instance, created, **kwargs):
    """
    Fired after every Message save.
    Only broadcasts newly created messages (not updates).
    """
    if not created:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return  # Channel layer not configured — skip silently

    # Push the message to all WebSocket clients in the chat group
    async_to_sync(channel_layer.group_send)(
        CHAT_GROUP,
        {
            'type': 'chat_message',
            'message': instance.content,
            'sender': instance.sender.email,
        },
    )

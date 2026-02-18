"""
users/models.py

Defines:
  - User  : custom user extending AbstractUser
  - OTP   : one-time password linked to a user
  - Message: chat message for the real-time chat system
"""

import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------
class User(AbstractUser):
    """
    Extends Django's AbstractUser.
    `username` is kept (required by AbstractUser) but email is the
    primary identifier for login / uniqueness.
    """
    # Override email to enforce uniqueness
    email = models.EmailField(unique=True)

    name = models.CharField(max_length=150, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(
        upload_to='profile_images/', null=True, blank=True
    )

    # Geographic coordinates for the Nearby Users feature
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Becomes True only after OTP verification
    is_verified = models.BooleanField(default=False)

    # Use email as the login field
    USERNAME_FIELD = 'email'
    # username is still required by AbstractUser; keep it in REQUIRED_FIELDS
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# OTP Model
# ---------------------------------------------------------------------------
class OTP(models.Model):
    """
    Stores a 6-digit OTP for a user.
    OTPs expire after 5 minutes (checked via is_expired()).
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='otps'
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        """Return True if the OTP was created more than 5 minutes ago."""
        expiry_time = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiry_time

    @staticmethod
    def generate_code():
        """Generate a random 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"OTP({self.user.email}, {self.code})"


# ---------------------------------------------------------------------------
# Message Model (Real-Time Chat)
# ---------------------------------------------------------------------------
class Message(models.Model):
    """
    Represents a chat message sent by a user.
    A post_save signal (in signals.py) broadcasts new messages
    to the WebSocket group automatically.
    """
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.email}: {self.content[:40]}"

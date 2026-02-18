"""
users/apps.py

AppConfig — connects signals when the app is ready.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Import signals module so the @receiver decorators are registered
        import users.signals  # noqa: F401

"""
WSGI config for core project (used by traditional WSGI servers).
For WebSocket support use asgi.py instead.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

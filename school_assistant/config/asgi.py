"""ASGI config.

Required because the AI chatbot uses WebSockets (via Django Channels) for
real-time message delivery, in addition to normal HTTP request/response.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# This must be created BEFORE importing anything that touches models, so
# Django's app registry is ready first.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack

# WebSocket enabled: route websocket connections to chat consumers.
# If chat/routing.py exists, prefer it; otherwise keep patterns empty.
try:
    from school_assistant.chat import routing as chat_routing

    websocket_urlpatterns = chat_routing.websocket_urlpatterns
except Exception:
    websocket_urlpatterns = []

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(websocket_urlpatterns),
    }
)


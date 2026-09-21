"""
ASGI config for atelier project.

Serve HTTP normal (django-ninja) e WebSocket (chat) no mesmo processo.
Em dev, o `daphne` (primeiro em INSTALLED_APPS) faz o `runserver` usar
isso automaticamente. Em produção, é isto que o Daphne serve (ver
docker-compose.prod.yml).
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atelier.config.settings.dev')

# `get_asgi_application()` precisa rodar (e o app registry do Django
# precisa estar populado) ANTES de importar qualquer coisa que toque em
# models — por isso a importação de `chat.routing` e do middleware vem
# depois desta linha, não no topo do arquivo.
django_asgi_app = get_asgi_application()

from atelier.apps.chat.middleware import JWTAuthMiddlewareStack  # noqa: E402
from atelier.apps.chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
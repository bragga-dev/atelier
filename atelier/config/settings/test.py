"""
Settings de teste — banco sqlite em memória (não depende de Postgres
rodando), Celery síncrono (sem broker), channel layer em memória (sem
depender de Redis rodando), rate limit desligado e envio de e-mail em
memória. Nada aqui chama serviço externo de verdade; a Asaas é sempre
mockada nos testes.
"""
from .base import *  # noqa

DEBUG = False

SECRET_KEY = env("SECRET_KEY", default="test-secret-key")

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_CACHE_BACKEND = "memory"

# Channels: em memória, sem depender de Redis rodando.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Nota sobre storage: os models com FileField/ImageField do projeto
# (MessageAttachment, ProductImage...) fixam `storage=PrivateFilesStorage()`
# / `MediaFilesStorage()` direto no campo — não usam o `STORAGES["default"]`
# das settings. Por isso, ao contrário de banco/cache/broker, não dá pra
# "trocar o storage" por aqui; testes que gravam arquivo de verdade
# precisam substituir o storage do campo em tempo de teste (ver
# `unittest.mock.patch` nos testes que envolvem upload).

# django-ratelimit: desliga nos testes pra não derrubar chamadas repetidas
# de teste que batem no mesmo endpoint várias vezes.
RATELIMIT_ENABLE = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
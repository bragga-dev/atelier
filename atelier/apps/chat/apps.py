from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = "atelier.apps.chat"
    label = "chat"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Chat"
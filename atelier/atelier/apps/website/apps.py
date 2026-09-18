
from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    name = 'atelier.apps.website'
    label = 'website'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Web Site'



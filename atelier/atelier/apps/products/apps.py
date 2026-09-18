from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = 'atelier.apps.products'
    label = 'products'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Produtos'
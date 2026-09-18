
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = 'atelier.apps.payments'
    label = 'payments'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Pagamentos'



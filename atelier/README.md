export DJANGO_SETTINGS_MODULE=atelier.config.settings.test
pytest atelier/apps/payments/tests --cov=atelier/apps/payments --cov-report=term-missing
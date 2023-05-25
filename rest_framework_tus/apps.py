from django.apps import AppConfig


class RestFrameworkTusConfig(AppConfig):
    name = 'rest_framework_tus'

    def ready(self):
        from . import receivers  # noqa: F401

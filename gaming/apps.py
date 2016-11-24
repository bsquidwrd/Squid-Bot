from django.apps import AppConfig


class GamingConfig(AppConfig):
    name = 'gaming'

    def ready(self):
        import gaming.signals

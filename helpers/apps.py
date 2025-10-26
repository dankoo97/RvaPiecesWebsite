from django.apps import AppConfig


class HelpersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "helpers"

    def ready(self):
        from helpers import db_sync

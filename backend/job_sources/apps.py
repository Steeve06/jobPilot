from django.apps import AppConfig


class JobSourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'job_sources'

    def ready(self):
        import job_sources.signals  # noqa: F401
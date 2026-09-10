from django.core.management.base import BaseCommand, CommandError

from job_sources.models import JobSource
from ingestion.service import poll_source, PollSourceError


class Command(BaseCommand):
    help = 'Manually poll a single JobSource by ID (Celery-scheduled polling arrives in Sprint 14)'

    def add_arguments(self, parser):
        parser.add_argument('source_id', type=int)

    def handle(self, *args, **options):
        try:
            job_source = JobSource.objects.get(id=options['source_id'])
        except JobSource.DoesNotExist:
            raise CommandError(f'JobSource {options["source_id"]} does not exist')

        self.stdout.write(f'Polling {job_source.company_name} ({job_source.type})...')

        try:
            result = poll_source(job_source)
        except PollSourceError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {result["created"]}, skipped {result["skipped_duplicates"]} duplicates.'
        ))
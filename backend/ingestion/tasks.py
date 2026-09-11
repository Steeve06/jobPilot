import logging

from celery import shared_task

from job_sources.models import JobSource
from .service import poll_source, PollSourceError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, autoretry_for=(PollSourceError,),
    retry_backoff=True, retry_kwargs={'max_retries': 3},
)
def poll_source_task(self, job_source_id):
    try:
        job_source = JobSource.objects.get(id=job_source_id, enabled=True)
    except JobSource.DoesNotExist:
        logger.info(f'JobSource {job_source_id} not found or disabled, skipping.')
        return

    try:
        result = poll_source(job_source)
        logger.info(f'Polled {job_source.company_name}: {result}')
    except PollSourceError as exc:
        logger.error(f'Poll failed for {job_source.company_name}: {exc}')
        raise
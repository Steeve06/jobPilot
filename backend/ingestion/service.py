import requests
from django.utils import timezone

from postings.models import JobPosting
from .adapters import get_adapter
from .adapters.base import compute_dedupe_hash


class PollSourceError(Exception):
    pass


def poll_source(job_source):
    """
    Fetches postings for one JobSource via its adapter, deduplicates
    against existing JobPosting rows, and creates new ones. Returns a
    small summary dict for logging/visibility.

    Raises PollSourceError with a clear message on any fetch failure
    (bad config, unreachable API, unexpected response shape) rather
    than letting the raw underlying exception propagate — this matters
    once polling is automated (Sprint 14) and one bad source shouldn't
    crash the whole task queue.
    """
    try:
        adapter = get_adapter(job_source.type)
    except ValueError as exc:
        raise PollSourceError(f'{job_source.company_name}: {exc}') from exc

    try:
        normalized_postings = adapter.fetch_postings(job_source)
    except requests.exceptions.HTTPError as exc:
        raise PollSourceError(
            f'{job_source.company_name} ({job_source.type}): API returned '
            f'{exc.response.status_code}. Check the board_slug in this source\'s config.'
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise PollSourceError(
            f'{job_source.company_name} ({job_source.type}): network error — {exc}'
        ) from exc
    except ValueError as exc:
        raise PollSourceError(f'{job_source.company_name} ({job_source.type}): {exc}') from exc


    created_count = 0
    skipped_count = 0

    for posting_data in normalized_postings:
        dedupe_hash = compute_dedupe_hash(
            posting_data.company, posting_data.title, posting_data.location,
        )

        if JobPosting.objects.filter(dedupe_hash=dedupe_hash).exists():
            skipped_count += 1
            continue

        JobPosting.objects.create(
            source=job_source,
            external_id=posting_data.external_id,
            company=posting_data.company,
            title=posting_data.title,
            location=posting_data.location,
            remote=posting_data.remote,
            url=posting_data.url,
            description_raw=posting_data.description_raw,
            description_normalized=posting_data.description_normalized,
            dedupe_hash=dedupe_hash,
        )
        created_count += 1

    job_source.last_polled_at = timezone.now()
    job_source.save(update_fields=['last_polled_at'])

    return {'created': created_count, 'skipped_duplicates': skipped_count}
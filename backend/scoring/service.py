from django.conf import settings
from django.utils import timezone

from ai.models import AICallLog
from ai.service import AIServiceError, score_posting_fit
from postings.models import JobPosting, ScoringLog
from search_profiles.models import SearchProfile
from .hard_filter import apply_hard_filters


SCORE_THRESHOLD = 40  # per FR9: below this, stored but not surfaced in main feed


def score_unscored_postings(profile, resume, on_progress=None):
    """
    on_progress: optional callable(current_index, total, posting) invoked
    after each posting is scored — lets callers (e.g. the management
    command) show progress instead of appearing frozen during long runs.
    """
    daily_cap = getattr(settings, 'AI_DAILY_SCORING_CAP', 100)
    today_count = AICallLog.objects.filter(
        purpose='scoring', profile=profile, created_at__date=timezone.now().date(),
    ).count()
    remaining_budget = max(daily_cap - today_count, 0)

    if remaining_budget == 0:
        return {'scored': 0, 'skipped_cap': True, 'filtered_out': 0, 'eligible': 0}

    unscored = JobPosting.objects.filter(
        source__profile=profile, fit_score__isnull=True,
    )
    active_search_profiles = list(SearchProfile.objects.filter(profile=profile, active=True))
    eligible_qs = apply_hard_filters(unscored, active_search_profiles)

    unscored_count = unscored.count()
    eligible_ids = list(eligible_qs.values_list('id', flat=True)[:remaining_budget])
    eligible_total_count = eligible_qs.count()
    filtered_out_count = unscored_count - eligible_total_count

    scored_count = 0
    total_to_process = len(eligible_ids)
    for index, posting in enumerate(JobPosting.objects.filter(id__in=eligible_ids), start=1):
        try:
            result = score_posting_fit(profile, resume, posting)
        except AIServiceError:
            if on_progress:
                on_progress(index, total_to_process, posting, error=True)
            continue

        posting.fit_score = result['fit_score']
        posting.fit_rationale = result['rationale']
        posting.missing_skills = result['missing_skills']
        posting.save(update_fields=['fit_score', 'fit_rationale', 'missing_skills'])

        ScoringLog.objects.create(
            posting=posting,
            input_payload=result['_input_payload'],
            output_payload=result['_output_payload'],
            model_version=settings.AI_MODEL,
            latency_ms=result['_latency_ms'],
        )
        scored_count += 1

        if on_progress:
            on_progress(index, total_to_process, posting, error=False)

    return {
        'scored': scored_count,
        'skipped_cap': eligible_total_count > remaining_budget,
        'filtered_out': filtered_out_count,
        'eligible': eligible_total_count,
    }
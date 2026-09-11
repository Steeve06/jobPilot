import logging

from celery import shared_task

from accounts.models import Profile
from resumes.models import Resume
from .service import score_unscored_postings

logger = logging.getLogger(__name__)


@shared_task
def score_postings_task(profile_id):
    try:
        profile = Profile.objects.get(id=profile_id)
        resume = profile.resume
    except (Profile.DoesNotExist, Resume.DoesNotExist):
        logger.info(f'Profile {profile_id} has no resume yet, skipping scoring.')
        return

    result = score_unscored_postings(profile, resume)
    logger.info(f'Scored {profile}: {result}')


@shared_task
def score_all_profiles_task():
    """Beat-scheduled entry point: fan out to one task per profile with a resume."""
    for profile_id in Resume.objects.values_list('profile_id', flat=True):
        score_postings_task.delay(profile_id)
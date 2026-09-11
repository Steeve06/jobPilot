import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import Profile
from applications.models import Application
from postings.models import JobPosting
from scoring.service import SCORE_THRESHOLD
from .models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_daily_digest_task():
    for profile in Profile.objects.all():
        _send_digest_for_profile(profile)


def _send_digest_for_profile(profile):
    new_matches = JobPosting.objects.filter(
        source__profile=profile,
        fit_score__gte=SCORE_THRESHOLD,
        digested=False,
    ).order_by('-fit_score')

    if not new_matches.exists():
        return

    lines = [f"{p.title} at {p.company} — {p.fit_score} FIT" for p in new_matches[:20]]
    body = "New high-fit matches:\n\n" + "\n".join(lines)

    Notification.objects.create(
        profile=profile, kind=Notification.Kind.WEEKLY_DIGEST,
        title=f'{new_matches.count()} new high-fit matches',
        body=body,
    )

    user_email = profile.user.email
    if user_email:
        try:
            send_mail(
                subject=f'JobPilot: {new_matches.count()} new high-fit matches',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
            )
        except Exception as exc:
            logger.error(f'Failed to send digest email to {user_email}: {exc}')

    new_matches.update(digested=True)


@shared_task
def stale_application_check_task():
    cutoff = timezone.now() - timedelta(days=settings.STALE_APPLICATION_DAYS)
    stale_applications = Application.objects.filter(
        status=Application.Status.APPLIED, updated_at__lt=cutoff,
    )

    for application in stale_applications:
        profile = application.posting.source.profile
        already_notified = Notification.objects.filter(
            profile=profile, kind=Notification.Kind.DEADLINE_REMINDER,
            body__contains=str(application.id),
        ).exists()
        if already_notified:
            continue

        days_idle = (timezone.now() - application.updated_at).days
        Notification.objects.create(
            profile=profile, kind=Notification.Kind.DEADLINE_REMINDER,
            title=f'{application.posting.company} — no update in {days_idle} days',
            body=f'Application {application.id} for {application.posting.title} at '
                 f'{application.posting.company} has been in "applied" status for {days_idle} days.',
        )
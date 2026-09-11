from django.db import models

from accounts.models import Profile


class Notification(models.Model):
    class Kind(models.TextChoices):
        HIGH_FIT_JOB = 'high_fit_job', 'High-fit job found'
        APPLICATION_ADVANCED = 'application_advanced', 'Application advanced'
        DEADLINE_REMINDER = 'deadline_reminder', 'Deadline reminder'
        SOURCE_POLL_FAILED = 'source_poll_failed', 'Source poll failed'
        WEEKLY_DIGEST = 'weekly_digest', 'Weekly digest'

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=30, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.profile})'
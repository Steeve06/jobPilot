from django.db import models

from accounts.models import Profile


class JobSource(models.Model):
    class SourceType(models.TextChoices):
        GREENHOUSE = 'greenhouse', 'Greenhouse'
        LEVER = 'lever', 'Lever'
        ASHBY = 'ashby', 'Ashby'
        REMOTEOK = 'remoteok', 'RemoteOK'
        RSS = 'rss', 'RSS'
        MANUAL_SCRAPE = 'manual_scrape', 'Manual scrape'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='job_sources',
    )
    company_name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=SourceType.choices)
    config = models.JSONField(default=dict, blank=True)  # e.g. {"board_slug": "stripe"}
    poll_interval_minutes = models.PositiveIntegerField(default=120)
    last_polled_at = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    is_auto_submit_eligible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return f'{self.company_name} ({self.get_type_display()})'
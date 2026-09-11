from django.db import models

from job_sources.models import JobSource


class JobPosting(models.Model):
    source = models.ForeignKey(
        JobSource,
        on_delete=models.CASCADE,
        related_name='postings',
    )
    external_id = models.CharField(max_length=255, blank=True)  # ID from the source's own system
    company = models.CharField(max_length=200)
    title = models.CharField(max_length=300)
    location = models.CharField(max_length=200, blank=True)
    remote = models.BooleanField(default=False)
    url = models.URLField(max_length=1000)

    description_raw = models.TextField(blank=True)
    description_normalized = models.TextField(blank=True)

    dedupe_hash = models.CharField(max_length=64, unique=True, db_index=True)

    posted_at = models.DateTimeField(null=True, blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)

    fit_score = models.PositiveSmallIntegerField(null=True, blank=True)  # 0-100
    fit_rationale = models.TextField(blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    digested = models.BooleanField(default=False)

    class Meta:
        ordering = ['-discovered_at']
        indexes = [
            models.Index(fields=['fit_score']),
            models.Index(fields=['source', 'discovered_at']),
        ]

    def __str__(self):
        return f'{self.title} @ {self.company}'
    
class ScoringLog(models.Model):
    posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='scoring_logs',
    )
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)
    model_version = models.CharField(max_length=100, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    cost_estimate = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'ScoringLog for {self.posting} @ {self.created_at}'
    
class PostingDecision(models.Model):
    class Decision(models.TextChoices):
        SAVED = 'saved', 'Saved'
        SKIPPED = 'skipped', 'Skipped'

    posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='decisions')
    profile = models.ForeignKey('accounts.Profile', on_delete=models.CASCADE, related_name='posting_decisions')
    decision = models.CharField(max_length=10, choices=Decision.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['posting', 'profile'], name='one_decision_per_profile_per_posting'),
        ]

    def __str__(self):
        return f'{self.profile} {self.decision} {self.posting}'
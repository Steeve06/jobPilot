from django.db import models


class AICallLog(models.Model):
    class Purpose(models.TextChoices):
        RESUME_EXTRACTION = 'resume_extraction', 'Resume Extraction'
        SCORING = 'scoring', 'Scoring'
        TAILORING = 'tailoring', 'Tailoring'

    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    profile = models.ForeignKey('accounts.Profile', on_delete=models.SET_NULL, null=True)
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)
    model_version = models.CharField(max_length=100, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    cost_estimate = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.purpose} @ {self.created_at}'
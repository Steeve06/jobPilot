from django.db import models

from accounts.models import Profile


class SearchProfile(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='search_profiles',
    )
    name = models.CharField(max_length=100)  # e.g. "Backend Track"
    title_keywords = models.JSONField(default=list, blank=True)
    excluded_keywords = models.JSONField(default=list, blank=True)
    yoe_min = models.PositiveIntegerField(null=True, blank=True)
    yoe_max = models.PositiveIntegerField(null=True, blank=True)
    locations = models.JSONField(default=list, blank=True)
    remote_ok = models.BooleanField(default=True)
    salary_floor = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-active', 'name']

    def __str__(self):
        return f'{self.name} ({self.profile})'
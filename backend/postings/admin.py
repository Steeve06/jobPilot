from django.contrib import admin

from .models import JobPosting, ScoringLog


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'source', 'fit_score', 'remote', 'discovered_at')
    list_filter = ('remote', 'source__type')
    search_fields = ('title', 'company')


@admin.register(ScoringLog)
class ScoringLogAdmin(admin.ModelAdmin):
    list_display = ('posting', 'latency_ms', 'cost_estimate', 'created_at')
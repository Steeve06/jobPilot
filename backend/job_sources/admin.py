from django.contrib import admin

from .models import JobSource


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'type', 'profile', 'enabled',
        'is_auto_submit_eligible', 'last_polled_at',
    )
    list_filter = ('type', 'enabled', 'is_auto_submit_eligible')
    search_fields = ('company_name',)
from django.contrib import admin

from .models import SearchProfile


@admin.register(SearchProfile)
class SearchProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'active', 'remote_ok', 'yoe_min', 'yoe_max')
    list_filter = ('active', 'remote_ok')
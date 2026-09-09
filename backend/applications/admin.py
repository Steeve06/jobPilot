from django.contrib import admin

from .models import Application, Note, StatusEvent


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('posting', 'status', 'submission_method', 'next_action_date', 'updated_at')
    list_filter = ('status', 'submission_method')
    inlines = [StatusEventInline, NoteInline]
from django.contrib import admin

from .models import Bullet, Experience, Project, Resume, TailoredResume, TailoringLog


class BulletInline(admin.TabularInline):
    model = Bullet
    extra = 1


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('profile', 'full_name', 'updated_at')
    search_fields = ('full_name', 'profile__name')


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'resume', 'start_date', 'end_date')
    inlines = [BulletInline]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'resume')
    inlines = [BulletInline]


@admin.register(TailoredResume)
class TailoredResumeAdmin(admin.ModelAdmin):
    list_display = ('posting', 'version_number', 'model_version', 'created_at')
    list_filter = ('model_version',)


@admin.register(TailoringLog)
class TailoringLogAdmin(admin.ModelAdmin):
    list_display = ('tailored_resume', 'latency_ms', 'cost_estimate', 'created_at')
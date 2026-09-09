from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Profile


class Resume(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='resume',
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)  # ["Go", "PostgreSQL", ...]
    education = models.JSONField(default=list, blank=True)  # small, rarely queried
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Resume: {self.profile}'


class Experience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null = "Present"
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_date']

    def __str__(self):
        return f'{self.title} @ {self.company}'


class Project(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Bullet(models.Model):
    experience = models.ForeignKey(
        Experience, on_delete=models.CASCADE, related_name='bullets',
        null=True, blank=True,
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='bullets',
        null=True, blank=True,
    )
    text = models.TextField()
    skill_tags = models.JSONField(default=list, blank=True)  # ["Go", "Kafka"]
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(experience__isnull=False, project__isnull=True) |
                    models.Q(experience__isnull=True, project__isnull=False)
                ),
                name='bullet_belongs_to_exactly_one_parent',
            )
        ]

    def clean(self):
        if bool(self.experience_id) == bool(self.project_id):
            raise ValidationError('A bullet must belong to exactly one of experience or project.')

    def __str__(self):
        return self.text[:50]
    
class TailoredResume(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='tailored_versions',
    )
    posting = models.ForeignKey(
        'postings.JobPosting',
        on_delete=models.CASCADE,
        related_name='tailored_resumes',
    )
    content = models.JSONField(default=dict)  # selected/reordered bullet refs + rewritten summary
    file_path = models.CharField(max_length=500, blank=True)  # rendered DOCX location
    model_version = models.CharField(max_length=100, blank=True)
    version_number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'TailoredResume v{self.version_number} for {self.posting}'


class TailoringLog(models.Model):
    tailored_resume = models.ForeignKey(
        TailoredResume,
        on_delete=models.CASCADE,
        related_name='logs',
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
        return f'TailoringLog for {self.tailored_resume}'
from django.db import models

from postings.models import JobPosting

class Application(models.Model):
    class Status(models.TextChoices):
        DISCOVERED = 'discovered', 'Discovered'
        TAILORING = 'tailoring', 'Tailoring'
        READY = 'ready', 'Ready'
        APPLIED = 'applied', 'Applied'
        OA_INTERVIEW = 'oa_interview', 'OA / Interview'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        GHOSTED = 'ghosted', 'Ghosted'

    class SubmissionMethod(models.TextChoices):
        API = 'api', 'API'
        MANUAL = 'manual', 'Manual'

    posting = models.OneToOneField(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='application',
    )
    tailored_resume = models.ForeignKey(
        'resumes.TailoredResume',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='applications',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DISCOVERED,
    )
    applied_at = models.DateTimeField(null=True, blank=True)
    submission_method = models.CharField(
        max_length=10, choices=SubmissionMethod.choices, null=True, blank=True,
    )
    next_action_date = models.DateField(null=True, blank=True)
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.posting} — {self.get_status_display()}'


class StatusEvent(models.Model):
    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        GMAIL_AUTO = 'gmail_auto', 'Gmail (auto-detected)'

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_events',
    )
    status = models.CharField(max_length=20, choices=Application.Status.choices)
    source = models.CharField(max_length=15, choices=Source.choices, default=Source.MANUAL)
    confirmed = models.BooleanField(default=True)  # False only for pending gmail_auto proposals
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        return f'{self.application} → {self.status} ({self.source})'


class Note(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:50]
    
class SubmissionLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='submission_logs')
    success = models.BooleanField()
    request_payload = models.JSONField(default=dict)
    response_payload = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'SubmissionLog for {self.application} ({"success" if self.success else "failed"})'
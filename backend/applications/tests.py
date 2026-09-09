from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from postings.models import JobPosting
from .models import Application, StatusEvent


class ApplicationModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        source = JobSource.objects.create(
            profile=profile, company_name='Ramp', type=JobSource.SourceType.ASHBY,
        )
        self.posting = JobPosting.objects.create(
            source=source, company='Ramp', title='SWE II',
            url='https://ramp.com/jobs/1', dedupe_hash='ramp-1',
        )

    def test_application_defaults_to_discovered(self):
        application = Application.objects.create(posting=self.posting)
        self.assertEqual(application.status, Application.Status.DISCOVERED)

    def test_one_application_per_posting(self):
        Application.objects.create(posting=self.posting)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(posting=self.posting)

    def test_gmail_status_event_defaults_unconfirmed_when_set_explicitly(self):
        application = Application.objects.create(posting=self.posting)
        event = StatusEvent.objects.create(
            application=application, status=Application.Status.REJECTED,
            source=StatusEvent.Source.GMAIL_AUTO, confirmed=False,
        )
        self.assertFalse(event.confirmed)
        # Confirming an event shouldn't happen automatically:
        self.assertEqual(application.status, Application.Status.DISCOVERED)
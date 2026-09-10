from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from postings.models import JobPosting
from .models import Application, StatusEvent
from config.test_utils import TwoProfileTestCase


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
        
class ApplicationScopingTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        source_a = JobSource.objects.create(
            profile=self.profile_a, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )
        source_b = JobSource.objects.create(
            profile=self.profile_b, company_name='Notion', type=JobSource.SourceType.LEVER,
        )
        self.posting_a = JobPosting.objects.create(
            source=source_a, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/1', dedupe_hash='a1',
        )
        self.posting_b = JobPosting.objects.create(
            source=source_b, company='Notion', title='Platform Engineer',
            url='https://notion.com/1', dedupe_hash='b1',
        )

    def test_cannot_create_application_against_another_profiles_posting(self):
        response = self.client.post('/api/applications/', {'posting': self.posting_b.id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('posting', response.data)

    def test_can_create_application_against_own_profiles_posting(self):
        response = self.client.post('/api/applications/', {'posting': self.posting_a.id}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_posting_field_is_write_once(self):
        application = Application.objects.create(posting=self.posting_a)
        response = self.client.patch(
            f'/api/applications/{application.id}/',
            {'posting': self.posting_b.id, 'next_action_date': '2026-09-15'},
            format='json',
        )
        application.refresh_from_db()
        self.assertEqual(application.posting_id, self.posting_a.id)  # unchanged
        self.assertEqual(str(application.next_action_date), '2026-09-15')  # this did update

    def test_list_only_shows_own_profiles_applications(self):
        Application.objects.create(posting=self.posting_a)
        Application.objects.create(posting=self.posting_b)
        response = self.client.get('/api/applications/')
        posting_ids = [row['posting'] for row in response.data]
        self.assertIn(self.posting_a.id, posting_ids)
        self.assertNotIn(self.posting_b.id, posting_ids)

class StatusEventAutoCreationTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        source = JobSource.objects.create(
            profile=self.profile_a, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )
        posting = JobPosting.objects.create(
            source=source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/1', dedupe_hash='se-1',
        )
        self.application = Application.objects.create(posting=posting)

    def test_status_change_creates_status_event(self):
        self.client.patch(
            f'/api/applications/{self.application.id}/', {'status': 'tailoring'}, format='json',
        )
        events = StatusEvent.objects.filter(application=self.application)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().status, 'tailoring')
        self.assertEqual(events.first().source, StatusEvent.Source.MANUAL)
        self.assertTrue(events.first().confirmed)

    def test_updating_non_status_field_does_not_create_status_event(self):
        self.client.patch(
            f'/api/applications/{self.application.id}/',
            {'next_action_date': '2026-09-20'}, format='json',
        )
        self.assertEqual(StatusEvent.objects.filter(application=self.application).count(), 0)

    def test_setting_same_status_again_does_not_duplicate_event(self):
        self.client.patch(
            f'/api/applications/{self.application.id}/', {'status': 'discovered'}, format='json',
        )
        self.assertEqual(StatusEvent.objects.filter(application=self.application).count(), 0)

    def test_multiple_status_changes_create_multiple_ordered_events(self):
        self.client.patch(f'/api/applications/{self.application.id}/', {'status': 'tailoring'}, format='json')
        self.client.patch(f'/api/applications/{self.application.id}/', {'status': 'ready'}, format='json')
        events = list(StatusEvent.objects.filter(application=self.application).order_by('occurred_at'))
        self.assertEqual([e.status for e in events], ['tailoring', 'ready'])


class NoteScopingTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        source_a = JobSource.objects.create(
            profile=self.profile_a, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )
        source_b = JobSource.objects.create(
            profile=self.profile_b, company_name='Notion', type=JobSource.SourceType.LEVER,
        )
        posting_a = JobPosting.objects.create(
            source=source_a, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/1', dedupe_hash='note-a1',
        )
        posting_b = JobPosting.objects.create(
            source=source_b, company='Notion', title='Platform Engineer',
            url='https://notion.com/1', dedupe_hash='note-b1',
        )
        self.app_a = Application.objects.create(posting=posting_a)
        self.app_b = Application.objects.create(posting=posting_b)

    def test_can_add_note_to_own_application(self):
        response = self.client.post(
            f'/api/applications/{self.app_a.id}/notes/', {'text': 'Recruiter call scheduled'}, format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_cannot_add_note_to_another_profiles_application(self):
        response = self.client.post(
            f'/api/applications/{self.app_b.id}/notes/', {'text': 'Should not work'}, format='json',
        )
        self.assertEqual(response.status_code, 404)

    def test_empty_note_text_rejected(self):
        response = self.client.post(
            f'/api/applications/{self.app_a.id}/notes/', {'text': '   '}, format='json',
        )
        self.assertEqual(response.status_code, 400)
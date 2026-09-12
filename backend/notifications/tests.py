from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Profile
from applications.models import Application
from job_sources.models import JobSource
from postings.models import JobPosting
from .models import Notification
from .tasks import send_daily_digest_task, stale_application_check_task

from config.test_utils import TwoProfileTestCase


class NotificationScopingTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        Notification.objects.create(profile=self.profile_a, kind='weekly_digest', title='Mine')
        Notification.objects.create(profile=self.profile_b, kind='weekly_digest', title='Not mine')

    def test_list_only_shows_own_notifications(self):
        response = self.client.get('/api/notifications/')
        titles = [n['title'] for n in response.data]
        self.assertIn('Mine', titles)
        self.assertNotIn('Not mine', titles)

    def test_mark_all_read_only_affects_own_notifications(self):
        self.client.post('/api/notifications/mark_all_read/')
        self.assertTrue(Notification.objects.get(title='Mine').read)
        self.assertFalse(Notification.objects.get(title='Not mine').read)
    def test_mark_read_only_affects_own_notification(self):
        mine = Notification.objects.get(title='Mine')
        response = self.client.post(f'/api/notifications/{mine.id}/mark_read/')
        self.assertEqual(response.status_code, 200)
        mine.refresh_from_db()
        self.assertTrue(mine.read)

    def test_cannot_mark_read_another_profiles_notification(self):
        theirs = Notification.objects.get(title='Not mine')
        response = self.client.post(f'/api/notifications/{theirs.id}/mark_read/')
        self.assertEqual(response.status_code, 404)
class DailyDigestTaskTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw', email='alex@x.com')
        self.profile = Profile.objects.create(user=user, name='Backend Track')
        source = JobSource.objects.create(
            profile=self.profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
        )
        self.high_fit = JobPosting.objects.create(
            source=source, company='TestCo', title='Backend Engineer',
            url='https://x.com/1', dedupe_hash='nd-1', fit_score=85, digested=False,
        )
        self.low_fit = JobPosting.objects.create(
            source=source, company='TestCo', title='Junior Support',
            url='https://x.com/2', dedupe_hash='nd-2', fit_score=20, digested=False,
        )

    @patch('notifications.tasks.send_mail')
    def test_digest_creates_notification_for_high_fit_postings_only(self, mock_send_mail):
        send_daily_digest_task()
        notification = Notification.objects.get(profile=self.profile, kind='weekly_digest')
        self.assertIn('Backend Engineer', notification.body)
        self.assertNotIn('Junior Support', notification.body)

    @patch('notifications.tasks.send_mail')
    def test_digest_marks_postings_as_digested(self, mock_send_mail):
        send_daily_digest_task()
        self.high_fit.refresh_from_db()
        self.assertTrue(self.high_fit.digested)

    @patch('notifications.tasks.send_mail')
    def test_already_digested_postings_are_not_included_again(self, mock_send_mail):
        self.high_fit.digested = True
        self.high_fit.save()
        send_daily_digest_task()
        self.assertFalse(Notification.objects.filter(profile=self.profile, kind='weekly_digest').exists())

    @patch('notifications.tasks.send_mail')
    def test_no_eligible_postings_sends_no_email(self, mock_send_mail):
        JobPosting.objects.all().update(digested=True)
        send_daily_digest_task()
        mock_send_mail.assert_not_called()

    @patch('notifications.tasks.send_mail')
    def test_email_send_failure_does_not_block_notification_creation(self, mock_send_mail):
        mock_send_mail.side_effect = Exception('SMTP down')
        send_daily_digest_task()  # should not raise
        self.assertTrue(Notification.objects.filter(profile=self.profile, kind='weekly_digest').exists())


class StaleApplicationCheckTaskTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        self.profile = Profile.objects.create(user=user, name='Backend Track')
        source = JobSource.objects.create(
            profile=self.profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
        )
        posting = JobPosting.objects.create(
            source=source, company='TestCo', title='Backend Engineer',
            url='https://x.com/1', dedupe_hash='sc-1',
        )
        self.application = Application.objects.create(posting=posting, status='applied')
        Application.objects.filter(id=self.application.id).update(
            updated_at=timezone.now() - timedelta(days=10),
        )

    def test_stale_application_creates_notification(self):
        stale_application_check_task()
        self.assertTrue(Notification.objects.filter(kind='deadline_reminder').exists())

    def test_recently_updated_application_does_not_trigger(self):
        Application.objects.filter(id=self.application.id).update(updated_at=timezone.now())
        stale_application_check_task()
        self.assertFalse(Notification.objects.filter(kind='deadline_reminder').exists())

    def test_running_twice_does_not_duplicate_notification(self):
        stale_application_check_task()
        stale_application_check_task()
        self.assertEqual(Notification.objects.filter(kind='deadline_reminder').count(), 1)

    def test_non_applied_status_does_not_trigger(self):
        self.application.status = 'ready'
        self.application.save()
        stale_application_check_task()
        self.assertFalse(Notification.objects.filter(kind='deadline_reminder').exists())
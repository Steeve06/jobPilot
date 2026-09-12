from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from config.test_utils import TwoProfileTestCase
from accounts.models import Profile
from job_sources.models import JobSource
from .models import JobPosting, PostingDecision
from unittest.mock import patch
from applications.models import Application
from resumes.models import Resume
class JobPostingDedupeTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )

    def test_duplicate_dedupe_hash_rejected(self):
        JobPosting.objects.create(
            source=self.source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/jobs/1', dedupe_hash='abc123',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobPosting.objects.create(
                    source=self.source, company='Stripe', title='Backend Engineer (dup)',
                    url='https://stripe.com/jobs/1-dup', dedupe_hash='abc123',
                )

    def test_fit_score_defaults_to_null_until_scored(self):
        posting = JobPosting.objects.create(
            source=self.source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/jobs/2', dedupe_hash='xyz789',
        )
        self.assertIsNone(posting.fit_score)
        
class PostingDecisionTests(TwoProfileTestCase):
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
            url='https://stripe.com/1', dedupe_hash='pd-a1', fit_score=92,
        )
        self.posting_b = JobPosting.objects.create(
            source=source_b, company='Notion', title='Platform Engineer',
            url='https://notion.com/1', dedupe_hash='pd-b1', fit_score=84,
        )

    def test_save_then_skip_updates_in_place_not_duplicate(self):
        self.client.post(f'/api/postings/{self.posting_a.id}/decide/', {'decision': 'saved'}, format='json')
        self.client.post(f'/api/postings/{self.posting_a.id}/decide/', {'decision': 'skipped'}, format='json')
        self.assertEqual(PostingDecision.objects.filter(posting=self.posting_a).count(), 1)
        self.assertEqual(
            PostingDecision.objects.get(posting=self.posting_a).decision, 'skipped',
        )

    def test_cannot_decide_on_another_profiles_posting(self):
        response = self.client.post(
            f'/api/postings/{self.posting_b.id}/decide/', {'decision': 'saved'}, format='json',
        )
        self.assertEqual(response.status_code, 404)  # not visible via get_queryset at all
        self.assertEqual(PostingDecision.objects.filter(posting=self.posting_b).count(), 0)

    def test_invalid_decision_value_rejected(self):
        response = self.client.post(
            f'/api/postings/{self.posting_a.id}/decide/', {'decision': 'maybe'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_status_filter_reflects_decision(self):
        self.client.post(f'/api/postings/{self.posting_a.id}/decide/', {'decision': 'saved'}, format='json')

        new_response = self.client.get('/api/postings/?status=new')
        saved_response = self.client.get('/api/postings/?status=saved')

        new_ids = [p['id'] for p in new_response.data]
        saved_ids = [p['id'] for p in saved_response.data]

        self.assertNotIn(self.posting_a.id, new_ids)
        self.assertIn(self.posting_a.id, saved_ids)
        
class TailorEndpointTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        self.profile = Profile.objects.create(user=user, name='Backend Track')
        Resume.objects.create(profile=self.profile, full_name='Alex', email='a@x.com')
        source = JobSource.objects.create(
            profile=self.profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
        )
        self.posting = JobPosting.objects.create(
            source=source, company='TestCo', title='Backend Engineer',
            url='https://x.com/1', dedupe_hash='tl-1',
        )
        self.client = self.client_class()
        self.client.login(username='alex', password='pw')

    @patch('postings.views.tailor_resume')
    def test_tailor_creates_draft_without_creating_application(self, mock_tailor):
        mock_tailor.return_value = {
            'content': {'full_name': 'Alex', 'experiences': [], 'projects': []},
            '_input_payload': {}, '_output_payload': {}, '_latency_ms': 100,
        }
        response = self.client.post(f'/api/postings/{self.posting.id}/tailor/')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Application.objects.filter(posting=self.posting).exists())

    @patch('postings.views.tailor_resume')
    def test_accept_creates_application_and_advances_status(self, mock_tailor):
        mock_tailor.return_value = {
            'content': {'full_name': 'Alex', 'experiences': [], 'projects': []},
            '_input_payload': {}, '_output_payload': {}, '_latency_ms': 100,
        }
        tailor_response = self.client.post(f'/api/postings/{self.posting.id}/tailor/')
        tailored_resume_id = tailor_response.data['tailored_resume_id']

        accept_response = self.client.post(f'/api/tailored-resumes/{tailored_resume_id}/accept/')
        self.assertEqual(accept_response.status_code, 200)

        application = Application.objects.get(posting=self.posting)
        self.assertEqual(application.status, 'tailoring')
        self.assertEqual(application.tailored_resume_id, tailored_resume_id)

    @patch('postings.views.tailor_resume')
    def test_accepting_again_does_not_regress_status_from_ready(self, mock_tailor):
        mock_tailor.return_value = {
            'content': {'full_name': 'Alex', 'experiences': [], 'projects': []},
            '_input_payload': {}, '_output_payload': {}, '_latency_ms': 100,
        }
        Application.objects.create(posting=self.posting, status='ready')
        tailor_response = self.client.post(f'/api/postings/{self.posting.id}/tailor/')
        tailored_resume_id = tailor_response.data['tailored_resume_id']

        self.client.post(f'/api/tailored-resumes/{tailored_resume_id}/accept/')

        application = Application.objects.get(posting=self.posting)
        self.assertEqual(application.status, 'ready')  # unchanged, only advances from discovered

    def test_tailor_without_resume_returns_400(self):
        Resume.objects.filter(profile=self.profile).delete()
        response = self.client.post(f'/api/postings/{self.posting.id}/tailor/')
        self.assertEqual(response.status_code, 400)
        
from datetime import timedelta

from django.utils import timezone


class DashboardSummaryTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        self.profile = Profile.objects.create(user=user, name='Backend Track')
        self.client = self.client_class()
        self.client.login(username='alex', password='pw')
        self.source = JobSource.objects.create(
            profile=self.profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
        )

    def test_summary_counts_new_postings_this_week(self):
        JobPosting.objects.create(
            source=self.source, company='TestCo', title='Engineer',
            url='https://x.com/1', dedupe_hash='ds-1',
        )
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['new_postings_this_week'], 1)

    def test_summary_excludes_postings_older_than_a_week(self):
        posting = JobPosting.objects.create(
            source=self.source, company='TestCo', title='Old Posting',
            url='https://x.com/2', dedupe_hash='ds-2',
        )
        JobPosting.objects.filter(id=posting.id).update(
            discovered_at=timezone.now() - timedelta(days=10),
        )
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.data['new_postings_this_week'], 0)

    def test_avg_fit_score_null_when_nothing_scored(self):
        response = self.client.get('/api/dashboard/summary/')
        self.assertIsNone(response.data['avg_fit_score'])

    def test_avg_fit_score_computed_correctly(self):
        JobPosting.objects.create(
            source=self.source, company='TestCo', title='A',
            url='https://x.com/3', dedupe_hash='ds-3', fit_score=80,
        )
        JobPosting.objects.create(
            source=self.source, company='TestCo', title='B',
            url='https://x.com/4', dedupe_hash='ds-4', fit_score=60,
        )
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.data['avg_fit_score'], 70.0)

    def test_summary_only_reflects_own_profile_data(self):
        other_user = User.objects.create_user(username='sam', password='pw')
        other_profile = Profile.objects.create(user=other_user, name='Other')
        other_source = JobSource.objects.create(
            profile=other_profile, company_name='OtherCo', type=JobSource.SourceType.LEVER,
        )
        JobPosting.objects.create(
            source=other_source, company='OtherCo', title='Not mine',
            url='https://x.com/5', dedupe_hash='ds-5',
        )
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.data['new_postings_this_week'], 0)
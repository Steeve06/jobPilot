from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from config.test_utils import TwoProfileTestCase
from accounts.models import Profile
from job_sources.models import JobSource
from .models import JobPosting, PostingDecision


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